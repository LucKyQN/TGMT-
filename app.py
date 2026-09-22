"""Ung dung local: webcam/video, HUD, doi bai, ghi demo va CSV."""
import argparse
import csv
import json
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import cv2
import numpy as np
from config import load_config
from exercise_engine import EXERCISES, ExerciseEngine, StarterBaseline, extract_measurement
from pose_backend import PoseBackend, ROOT, draw_skeleton

REP_FIELDS = ['segment', 'bai', 'rep', 'start_s', 'end_s', 'min_angle', 'min_body', 'max_lean', 'form', 'reason']
FRAME_FIELDS = ['segment', 'frame', 'time_s', 'bai', 'valid', 'side', 'angle_raw', 'angle', 'body',
                'lean', 'horizontal', 'stage', 'form_good', 'reps', 'plank_s', 'baseline_reps']


def write_csv(path, rows, fields):
    with Path(path).open('w', newline='', encoding='utf-8-sig') as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def put(canvas, text, xy, scale=0.7, color=(227, 233, 241), thickness=1):
    cv2.putText(canvas, text, xy, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def hud(frame, landmarks, engine, now, fps, model, last_result, recording):
    """HUD 1280x720; letterbox anh de giu ti le."""
    frame = frame.copy()
    draw_skeleton(frame, landmarks, engine.cfg.visibility)
    canvas = np.full((720, 1280, 3), (23, 18, 14), dtype=np.uint8)
    cv2.rectangle(canvas, (0, 0), (1279, 83), (39, 30, 22), -1)
    put(canvas, 'MOTION LAB', (30, 39), 1.0, (153, 240, 90), 2)
    put(canvas, 'IUH  /  THI GIAC MAY TINH  /  CHU DE 06', (30, 66), 0.48)
    put(canvas, f'{model.upper()}   {fps:4.1f} FPS   {now:6.1f}s', (842, 43), 0.7)
    h, w = frame.shape[:2]
    ratio = min(864 / w, 540 / h)
    resized = cv2.resize(frame, (round(w * ratio), round(h * ratio)))
    rh, rw = resized.shape[:2]
    x, y = 24 + (864-rw)//2, 105 + (540-rh)//2
    canvas[y:y+rh, x:x+rw] = resized
    x = 920
    put(canvas, engine.exercise.upper(), (x, 135), 1.15, (153, 240, 90), 2)
    put(canvas, engine.stage, (x, 174), 0.7)
    stats = engine.summary()
    if engine.exercise == 'plank':
        put(canvas, f"{stats['plank_s']:.1f}s", (x, 253), 1.8, (255, 255, 255), 3)
        put(canvas, 'THOI GIAN DAT', (x, 285), 0.6)
    else:
        put(canvas, f"{stats['reps']:02d}", (x, 255), 2.2, (255, 255, 255), 3)
        put(canvas, 'REP HOAN THANH', (x, 285), 0.6)
        put(canvas, f"DUNG {stats['dung']:02d}    SAI {stats['sai']:02d}", (x, 328), 0.7, (153, 240, 90), 2)
    m = engine.filtered
    for index, (key, title) in enumerate([('angle','GOC CHINH'), ('body','DUONG THAN'), ('lean','NGHIENG DOC'), ('horizontal','LECH NGANG')]):
        value = f'{m[key]:.1f}' if m else '--'
        put(canvas, f'{title}: {value}', (x, 383 + 34*index), 0.58)
    put(canvas, f'BEN: {engine.side or "--"}', (x, 540), 0.6)
    put(canvas, last_result[:27], (x, 580), 0.52, (110, 204, 255))
    if recording:
        put(canvas, 'REC  RAW + DEMO', (x, 624), 0.57, (110, 110, 255), 2)
    put(canvas, engine.feedback, (30, 677), 0.7, (110, 204, 255), 2)
    put(canvas, '1 SQUAT    2 PUSH-UP    3 PLANK    |    Q THOAT    |    GOC QUAY: BEN HONG', (30, 706), 0.53)
    return canvas


class TimelineRecorder:
    """Lap/bo frame theo timestamp, giu thoi luong webcam khi FPS bien thien."""
    def __init__(self, path, fps, size):
        self.writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'mp4v'), fps, size)
        if not self.writer.isOpened():
            raise RuntimeError(f'Khong mo duoc VideoWriter: {path}')
        self.fps, self.written, self.previous = fps, 0, None

    def push(self, frame, seconds):
        target = int(seconds * self.fps) + 1
        while self.written < target:
            self.writer.write(self.previous if self.previous is not None and self.written < target-1 else frame)
            self.written += 1
        self.previous = frame.copy()

    def close(self):
        self.writer.release()


def run_capture(source=0, exercise='squat', model='full', cfg=None, display=True,
                record=False, output=None, max_frames=0, fps_override=None):
    cfg = cfg or load_config()
    if not display and isinstance(source, int) and max_frames <= 0:
        raise ValueError('Webcam --no-display can --max-frames de co diem dung')
    output = Path(output) if output else ROOT / 'sessions' / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output.mkdir(parents=True, exist_ok=True)
    detector = PoseBackend(model)
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        detector.close()
        cap.release()
        raise RuntimeError('Khong mo duoc camera/video. Dong Zoom/Teams, kiem tra quyen camera, thu --source 1.')
    file_source = not isinstance(source, int)
    source_fps = float(fps_override or cap.get(cv2.CAP_PROP_FPS))
    if not np.isfinite(source_fps) or source_fps <= 0:
        cap.release()
        detector.close()
        raise ValueError('FPS nguon khong hop le; truyen --fps FPS_that')
    engine, baseline = ExerciseEngine(exercise, cfg), StarterBaseline(exercise)
    segment, segment_start = 1, 0.0
    segments, events, recorders = [], [], []
    frames, detected, infer_seconds, now = 0, 0, 0.0, 0.0
    start, first_capture = time.perf_counter(), None
    last_result, title = 'Cho hoan thanh rep', 'IUH | Motion Lab'
    aborted, error = False, None

    def save_segment():
        segments.append(dict(segment=segment, start_s=segment_start, end_s=now, **engine.summary(),
                             baseline_reps=baseline.count, baseline_plank_s=baseline.seconds))

    try:
        with (output / 'frames.csv').open('w', newline='', encoding='utf-8-sig') as logfile:
            log = csv.DictWriter(logfile, fieldnames=FRAME_FIELDS)
            log.writeheader()
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                capture_time = time.perf_counter()
                if first_capture is None:
                    first_capture = capture_time
                now = frames / source_fps if file_source else capture_time - first_capture
                tick = time.perf_counter()
                landmarks = detector.detect(frame, now)
                infer_seconds += time.perf_counter() - tick
                frames += 1
                detected += int(landmarks is not None)
                h, w = frame.shape[:2]
                measurement = extract_measurement(landmarks, w, h, engine.exercise, cfg, engine.side)
                event = engine.update(measurement, now)
                baseline.update(landmarks, now)
                if event:
                    events.append(dict(segment=segment, **event))
                    last_result = f"REP {event['rep']}: {event['reason']}"
                    print(f'{engine.exercise}: {last_result}', flush=True)
                m = engine.filtered or {}
                log.writerow(dict(segment=segment, frame=frames-1, time_s=round(now, 5), bai=engine.exercise,
                                  valid=int(measurement is not None), side=engine.side,
                                  angle_raw=measurement['angle'] if measurement else '',
                                  angle=m.get('angle',''), body=m.get('body',''), lean=m.get('lean',''),
                                  horizontal=m.get('horizontal',''), stage=engine.stage,
                                  form_good='' if engine.form_good is None else int(engine.form_good),
                                  reps=len(engine.reps), plank_s=engine.plank_seconds, baseline_reps=baseline.count))
                elapsed = time.perf_counter() - start
                if display or record:
                    canvas = hud(frame, landmarks, engine, now, frames / max(elapsed, 1e-6), model, last_result, record)
                    if record:
                        if not recorders:
                            recording_fps = source_fps if file_source else 20.0
                            recorders.append(TimelineRecorder(output / 'demo.mp4', recording_fps, (1280,720)))
                            recorders.append(TimelineRecorder(output / 'raw.mp4', recording_fps, (w,h)))
                        recorders[0].push(canvas, now)
                        recorders[1].push(frame, now)
                    if display:
                        cv2.imshow(title, canvas)
                        wait = max(1, int(1000 * ((frames / source_fps) - (time.perf_counter()-start)))) if file_source else 1
                        key = cv2.waitKey(min(wait, 100)) & 0xFF
                        if key == ord('q') or cv2.getWindowProperty(title, cv2.WND_PROP_VISIBLE) < 1:
                            aborted = True
                            break
                        if key in (ord('1'), ord('2'), ord('3')):
                            save_segment()
                            exercise = EXERCISES[key-ord('1')]
                            engine, baseline = ExerciseEngine(exercise, cfg), StarterBaseline(exercise)
                            segment, segment_start = segment+1, now
                            last_result = 'Da reset bai tap'
                if max_frames and frames >= max_frames:
                    aborted = True
                    break
    except Exception as exc:
        error = str(exc)
        raise
    finally:
        elapsed = time.perf_counter() - start
        save_segment()
        cap.release()
        detector.close()
        for recorder in recorders:
            recorder.close()
        if display:
            cv2.destroyAllWindows()
        write_csv(output / 'reps.csv', events, REP_FIELDS)
        write_csv(output / 'sessions.csv', segments, list(segments[0]))
        result = dict(source=str(source), model=model, config=asdict(cfg), frames=frames,
                      detected_frames=detected, source_fps=source_fps, duration_s=now,
                      processing_seconds=elapsed, processing_fps=frames/max(elapsed,1e-6),
                      inference_fps=frames/max(infer_seconds,1e-6),
                      interrupted=aborted, error=error, segments=segments, events=events,
                      versions=dict(opencv=cv2.__version__, numpy=np.__version__))
        (output / 'summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    if not frames:
        raise RuntimeError('Khong doc duoc khung hinh nao')
    print(f'Ket qua: {output}', flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(description='IUH Motion Lab: Squat / Push-up / Plank')
    parser.add_argument('--source', default='0', help='So camera hoac duong dan video')
    parser.add_argument('--exercise', choices=EXERCISES, default='squat')
    parser.add_argument('--model', choices=['lite','full','heavy'], default='full')
    parser.add_argument('--config', help='JSON ghi de cac nguong')
    parser.add_argument('--record', action='store_true', help='Luu raw.mp4 va demo.mp4')
    parser.add_argument('--no-display', action='store_true')
    parser.add_argument('--max-frames', type=int, default=0)
    parser.add_argument('--fps', type=float, help='FPS thuc cua video neu metadata sai')
    parser.add_argument('--output', help='Thu muc ket qua moi')
    args = parser.parse_args()
    source = int(args.source) if args.source.isdigit() else args.source
    try:
        run_capture(source, args.exercise, args.model, load_config(args.config), not args.no_display,
                    args.record, args.output, args.max_frames, args.fps)
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        parser.exit(1, f'LOI: {exc}\n')


if __name__ == '__main__':
    main()
