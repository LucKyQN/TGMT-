"""Goc pixel, loc tin hieu va may trang thai cho ba bai tap."""
import math
import numpy as np
from config import Config

EXERCISES = ('squat', 'pushup', 'plank')
SIDES = {
    'left': {'shoulder': 11, 'elbow': 13, 'wrist': 15, 'hip': 23, 'knee': 25, 'ankle': 27},
    'right': {'shoulder': 12, 'elbow': 14, 'wrist': 16, 'hip': 24, 'knee': 26, 'ankle': 28},
}


def calculate_angle(a, b, c):
    """Goc ABC tai B. None neu vector suy bien, tranh chia 0."""
    u, v = np.asarray(a, dtype=float) - b, np.asarray(c, dtype=float) - b
    denominator = np.linalg.norm(u) * np.linalg.norm(v)
    if not np.isfinite(denominator) or denominator < 1e-8:
        return None
    return float(np.degrees(np.arccos(np.clip(np.dot(u, v) / denominator, -1, 1))))


def required_names(exercise):
    return ('shoulder', 'hip', 'knee', 'ankle') if exercise == 'squat' else (
        ('shoulder', 'elbow', 'wrist', 'hip', 'ankle') if exercise == 'pushup'
        else ('shoulder', 'hip', 'ankle'))


def extract_measurement(landmarks, width, height, exercise, cfg, preferred=None):
    """Chon tong visibility cao nhat; giu ben cu neu chenh lech < 0.3.

    Ben thay doi se duoc engine reset de khong ghep hai chan/tay thanh mot rep.
    """
    if not landmarks:
        return None
    names = required_names(exercise)
    candidates = {}
    for side, indices in SIDES.items():
        points = [landmarks[indices[n]] for n in names]
        if all(p.visibility >= cfg.visibility and p.presence >= cfg.presence and
               0 <= p.x <= 1 and 0 <= p.y <= 1 for p in points):
            candidates[side] = sum(p.visibility for p in points)
    if not candidates:
        return None
    side = max(candidates, key=candidates.get)
    if preferred in candidates and candidates[side] - candidates[preferred] < 0.3:
        side = preferred
    pts = {n: np.array([landmarks[i].x * width, landmarks[i].y * height])
           for n, i in SIDES[side].items()}
    shoulder, hip, ankle = (pts[n] for n in ('shoulder', 'hip', 'ankle'))
    body = calculate_angle(shoulder, hip, ankle)
    lean = calculate_angle(shoulder, hip, hip + [0, -100])
    delta = shoulder - hip
    horizontal = math.degrees(math.atan2(abs(delta[1]), abs(delta[0])))
    if exercise == 'squat':
        angle = calculate_angle(hip, pts['knee'], ankle)
    elif exercise == 'pushup':
        angle = calculate_angle(shoulder, pts['elbow'], pts['wrist'])
    else:
        angle = body
    if any(v is None or not math.isfinite(v) for v in (angle, body, lean, horizontal)):
        return None
    return dict(angle=angle, body=body, lean=lean, horizontal=horizontal, side=side)


class ExerciseEngine:
    def __init__(self, exercise='squat', config=None):
        if exercise not in EXERCISES:
            raise ValueError(exercise)
        self.exercise, self.cfg = exercise, (config or Config()).validate()
        self.reps = []
        self.plank_seconds = 0.0
        self.observed_frames = self.good_frames = 0
        self.reset_tracking()

    def reset_tracking(self):
        """Khong xoa lich su; chi huy chu ky dang do khi mat dau/doi ben."""
        self.stage = 'WAIT_UP' if self.exercise != 'plank' else 'WAIT_HOLD'
        self.filtered = None
        self.side = None
        self.last_time = None
        self.pending = None
        self.pending_since = None
        self.candidate_since = None
        self.candidate_frames = 0
        self.started = None
        self.start_extrema = None
        self.min_angle, self.min_body, self.max_lean = 180.0, 180.0, 0.0
        self.feedback = 'Cho tu the bat dau'
        self.form_good = None

    def _confirmed(self, target, now):
        if target != self.pending:
            self.pending, self.pending_since = target, now
        return target is not None and now - self.pending_since >= self.cfg.transition_seconds

    def update(self, measurement, now):
        if not math.isfinite(now):
            raise ValueError('Timestamp khong hop le')
        if self.last_time is not None and now <= self.last_time:
            raise ValueError('Timestamp phai tang')
        if measurement is None:
            self.reset_tracking()
            self.feedback = 'MAT DAU - can thay ro cac khop'
            return None
        if self.last_time is not None and now - self.last_time > self.cfg.max_gap_seconds:
            self.reset_tracking()
        if self.side is not None and measurement['side'] != self.side:
            self.reset_tracking()
        self.side = measurement['side']
        dt = 0.0 if self.last_time is None else now - self.last_time
        self.last_time = now
        raw = {k: measurement[k] for k in ('angle', 'body', 'lean', 'horizontal')}
        if not all(math.isfinite(v) for v in raw.values()):
            self.reset_tracking()
            return None
        alpha = 1 - math.exp(-dt / self.cfg.ema_seconds)
        self.filtered = raw.copy() if self.filtered is None else {
            k: self.filtered[k] + alpha * (v - self.filtered[k]) for k, v in raw.items()}
        m = self.filtered
        self.observed_frames += 1
        if self.exercise == 'plank':
            # Raw gate bo sung de dung dong ho ngay khi form sai, khong cho EMA keo dai.
            c = self.cfg.plank
            good = all(x['body'] > c.min_body and x['horizontal'] < c.max_horizontal for x in (m, raw))
            self.form_good = good
            self.good_frames += int(good)
            if not good:
                self.stage = 'BAD_FORM'
                self.candidate_since, self.candidate_frames = None, 0
                self.feedback = 'Can than thang va gan nam ngang'
            else:
                self.candidate_frames += 1
                if self.candidate_since is None:
                    self.candidate_since = now
                if (now - self.candidate_since >= c.confirm_seconds and
                        self.candidate_frames >= c.confirm_frames):
                    # Khong tinh lui khoang xac nhan; chi cong cac khoang HOLD lien tuc.
                    if self.stage == 'HOLD':
                        self.plank_seconds += dt
                    self.stage, self.feedback = 'HOLD', 'DAT - dang tinh thoi gian'
                else:
                    self.stage, self.feedback = 'CONFIRM', 'Giu on dinh de bat dau'
            return None

        c = getattr(self.cfg, self.exercise)
        if self.exercise == 'pushup' and m['horizontal'] > c.max_horizontal:
            self.reset_tracking()
            self.feedback = 'Can tu the hit dat gan nam ngang'
            return None
        self.form_good = m['lean'] <= c.max_lean if self.exercise == 'squat' else m['body'] > c.min_body
        self.good_frames += int(self.form_good)
        active = self.stage in ('DESCENDING', 'DOWN', 'RETURNING')
        if active:
            self.min_angle = min(self.min_angle, m['angle'])
            self.min_body = min(self.min_body, m['body'])
            self.max_lean = max(self.max_lean, m['lean'])
            if now - self.started > self.cfg.max_rep_seconds:
                self.reset_tracking()
                self.feedback = 'Qua thoi gian mot rep - ve tu the len'
                return None
            if m['angle'] < c.down:
                self.stage = 'DOWN'
            elif self.stage == 'DOWN' and m['angle'] > c.down + 10:
                self.stage = 'RETURNING'
        target = None
        if self.stage == 'UP' and m['angle'] < c.start:
            target = 'START'
        elif self.stage != 'UP' and m['angle'] > c.up:
            target = 'UP'
        event = None
        if target == 'START':
            if self.pending != 'START':
                self.start_extrema = (m['angle'], m['body'], m['lean'])
            else:
                a, b, l = self.start_extrema
                self.start_extrema = (min(a,m['angle']), min(b,m['body']), max(l,m['lean']))
        if self._confirmed(target, now):
            if target == 'START':
                self.stage, self.started = 'DESCENDING', self.pending_since
                self.min_angle, self.min_body, self.max_lean = self.start_extrema
            else:
                if active and now - self.started >= self.cfg.min_rep_seconds:
                    reasons = []
                    if self.min_angle >= c.down:
                        reasons.append('SHALLOW')
                    if self.exercise == 'squat' and self.max_lean > c.max_lean:
                        reasons.append('LEAN')
                    if self.exercise == 'pushup' and self.min_body <= c.min_body:
                        reasons.append('BODY_LINE')
                    event = dict(bai=self.exercise, rep=len(self.reps) + 1,
                                 start_s=round(self.started, 4), end_s=round(now, 4),
                                 min_angle=round(self.min_angle, 2), min_body=round(self.min_body, 2),
                                 max_lean=round(self.max_lean, 2), form='sai' if reasons else 'dung',
                                 reason='+'.join(reasons) or 'OK')
                    self.reps.append(event)
                self.stage = 'UP'
            self.pending = None
        self.feedback = ('Can chinh do nghieng/duong than' if not self.form_good else
                         'Ve tu the len de hoan thanh rep' if self.stage != 'UP' else 'San sang')
        if self.stage == 'WAIT_UP':
            self.feedback = 'Duoi thang goi/tay de bat dau'
        return event

    def summary(self):
        return dict(bai=self.exercise, reps=len(self.reps),
                    dung=sum(r['form'] == 'dung' for r in self.reps),
                    sai=sum(r['form'] == 'sai' for r in self.reps),
                    plank_s=round(self.plank_seconds, 4), observed_frames=self.observed_frames,
                    good_frames=self.good_frames)


class StarterBaseline:
    """Squat: dung logic starter, goc normalized, chan trai, dem khi xuong.

    Pushup/plank la baseline MO RONG, khong phai starter cua de.
    Baseline khong co nhan form: khong duoc bao cao F1 form cho baseline.
    """
    def __init__(self, exercise):
        self.exercise, self.count, self.stage = exercise, 0, None
        self.seconds, self.previous_good, self.last_time = 0.0, False, None

    def update(self, landmarks, now):
        good = False
        if landmarks:
            ids = (23, 25, 27) if self.exercise == 'squat' else ((11, 13, 15) if self.exercise == 'pushup' else (11, 23, 27))
            angle = calculate_angle(*[[landmarks[i].x, landmarks[i].y] for i in ids])
            if angle is not None:
                if self.exercise == 'plank':
                    good = angle > 160
                else:
                    if angle > 160:
                        self.stage = 'up'
                    if angle < (100 if self.exercise == 'squat' else 90) and self.stage == 'up':
                        self.stage = 'down'
                        self.count += 1
        if good and self.previous_good and self.last_time is not None:
            self.seconds += now - self.last_time
        self.previous_good, self.last_time = good, now
