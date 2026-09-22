"""Danh gia video da gan nhan; khong tu suy dien ground truth tu ten file."""
import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
import numpy as np
from app import run_capture, write_csv
from config import load_config
from exercise_engine import EXERCISES


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def form_metrics(pairs):
    """Hang: that dung/sai; cot: du doan dung/sai/unknown. Unknown khong bi an."""
    matrix = [[0, 0, 0], [0, 0, 0]]
    for actual, predicted in pairs:
        if actual not in ('dung', 'sai'):
            continue
        matrix[('dung', 'sai').index(actual)][('dung', 'sai', 'unknown').index(predicted)] += 1
    n = sum(map(sum, matrix))
    per_class = {}
    for i, name in enumerate(('dung', 'sai')):
        tp, fp, fn = matrix[i][i], matrix[1-i][i], sum(matrix[i]) - matrix[i][i]
        precision = tp / (tp+fp) if tp+fp else 0.0
        recall = tp / (tp+fn) if tp+fn else 0.0
        per_class[name] = dict(precision=precision, recall=recall,
                              f1=2*precision*recall/(precision+recall) if precision+recall else 0.0,
                              support=sum(matrix[i]))
    return dict(n=n, rows=['dung','sai'], columns=['dung','sai','unknown'], confusion_matrix=matrix,
                coverage=(n-matrix[0][2]-matrix[1][2])/n if n else None,
                accuracy=(matrix[0][0]+matrix[1][1])/n if n else None,
                per_class=per_class, macro_f1=np.mean([v['f1'] for v in per_class.values()]).item() if n else None)


def match_reps(truth, predicted, tolerance):
    """Ghep 1-1 theo thu tu thoi gian; toi da so cap, sau do toi thieu sai lech.

    Dynamic programming tranh ghep tham lam lam mat mot cap hop le.
    """
    truth = sorted(truth, key=lambda r: float(r['end_s']))
    predicted = sorted(predicted, key=lambda r: float(r['end_s']))
    n, m = len(truth), len(predicted)
    dp = [[(0, 0.0, []) for _ in range(m+1)] for _ in range(n+1)]
    for i in range(1, n+1):
        for j in range(1, m+1):
            options = [dp[i-1][j], dp[i][j-1]]
            distance = abs(float(truth[i-1]['end_s']) - float(predicted[j-1]['end_s']))
            if distance <= tolerance:
                count, cost, matches = dp[i-1][j-1]
                options.append((count+1, cost-distance, matches+[(i-1,j-1)]))
            dp[i][j] = max(options, key=lambda x: (x[0], x[1]))
    matches = dp[n][m][2]
    pairs = [(truth[i]['form'], predicted[j]['form']) for i,j in matches]
    paired_truth = {i for i,_ in matches}
    pairs.extend((r['form'], 'unknown') for i,r in enumerate(truth) if i not in paired_truth)
    return dict(matched=len(matches), missed=n-len(matches), extra=m-len(matches), pairs=pairs)


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        # Tach nguon va bai; ALL chi de tham khao, khong thay the bang tach nguon.
        groups[(row['model'], row['nguon'], row['bai'])].append(row)
    result = []
    for (model, source, exercise), group in sorted(groups.items()):
        count_errors = [r['abs_error'] for r in group if r['abs_error'] != '']
        baseline_errors = [r['baseline_abs_error'] for r in group if r['baseline_abs_error'] != '']
        time_errors = [r['plank_abs_error_s'] for r in group if r['plank_abs_error_s'] != '']
        base_time = [r['baseline_plank_abs_error_s'] for r in group if r['baseline_plank_abs_error_s'] != '']
        metrics = form_metrics([(r['form_true'], r['form_pred']) for r in group])
        total_seconds = sum(r['processing_seconds'] for r in group)
        mean = lambda values: float(np.mean(values)) if values else None
        result.append(dict(model=model, nguon=source, bai=exercise, videos=len(group),
                           count_mae=mean(count_errors), exact_count_rate=mean([e == 0 for e in count_errors]),
                           baseline_count_mae=mean(baseline_errors),
                           baseline_exact_count_rate=mean([e == 0 for e in baseline_errors]),
                           plank_mae_s=mean(time_errors), baseline_plank_mae_s=mean(base_time),
                           processing_fps=sum(r['frames'] for r in group)/total_seconds,
                           form_video=metrics))
    return result


def main():
    p = argparse.ArgumentParser(description='Batch: baseline vs improved; lite/full/heavy')
    p.add_argument('--videos', type=Path, default=Path('data/videos'))
    p.add_argument('--ground-truth', type=Path, default=Path('data/ground_truth.csv'))
    p.add_argument('--rep-truth', type=Path, help='CSV video,rep,end_s,form')
    p.add_argument('--models', nargs='+', choices=['lite','full','heavy'], default=['full'])
    p.add_argument('--split', choices=['dev','test','all'], default='test')
    p.add_argument('--config')
    p.add_argument('--tolerance', type=float, default=0.75)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if args.tolerance <= 0:
        p.error('tolerance phai duong')
    cfg = load_config(args.config)
    output = args.output or Path('evaluation') / datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    output.mkdir(parents=True, exist_ok=False)
    truth = read_csv(args.ground_truth)
    reps_by_video = defaultdict(list)
    if args.rep_truth:
        for r in read_csv(args.rep_truth):
            if r['form'] not in ('dung','sai') or not np.isfinite(float(r['end_s'])):
                p.error('Nhan rep phai dung/sai va end_s huu han')
            reps_by_video[r['video']].append(r)
    rows, failures, rep_results = [], [], []
    seen = set()
    discovered = {str(f.relative_to(args.videos)).replace('\\','/') for f in args.videos.rglob('*')
                  if f.suffix.lower() in ('.mp4','.avi','.mov','.mkv')}
    for index, gt in enumerate(truth):
        if args.split != 'all' and gt.get('split', 'test') != args.split:
            continue
        try:
            video = gt['video'].replace('\\','/')
            exercise = gt['bai']
            if video in seen:
                raise ValueError('Video lap trong ground truth')
            seen.add(video)
            if exercise not in EXERCISES:
                raise ValueError('bai phai squat/pushup/plank')
            label = gt['form'].strip()
            if label not in ('dung','sai','mixed','unknown',''):
                raise ValueError('form phai dung/sai/mixed/unknown hoac rong')
            true_count = int(gt['so_rep_that']) if exercise != 'plank' else None
            true_time = float(gt['plank_giay_that']) if exercise == 'plank' else None
            if true_count is not None and true_count < 0:
                raise ValueError('so_rep_that phai >= 0')
            if true_time is not None and (not np.isfinite(true_time) or true_time < 0):
                raise ValueError('plank_giay_that phai huu han va >= 0')
            if not (args.videos / video).is_file():
                raise FileNotFoundError(video)
            if video in reps_by_video and len(reps_by_video[video]) != true_count:
                raise ValueError('So nhan rep khong khop so_rep_that')
        except (ValueError, KeyError, FileNotFoundError) as exc:
            failures.append(dict(video=gt.get('video','?'), model='all', error=str(exc)))
            continue
        for model in args.models:
            try:
                result = run_capture(str(args.videos/video), exercise, model, cfg, display=False,
                                     output=output / f'{index:03d}_{model}',
                                     fps_override=float(gt['fps']) if gt.get('fps') else None)
                s = result['segments'][0]
                coverage = s['observed_frames']/result['frames']
                if coverage < 0.5 or (exercise != 'plank' and s['reps'] == 0):
                    form_pred = 'unknown'
                elif exercise == 'plank':
                    form_pred = 'dung' if s['good_frames']/result['frames'] >= cfg.video_form_fraction else 'sai'
                else:
                    form_pred = 'dung' if s['sai'] == 0 else 'sai'
                row = dict(video=video, bai=exercise, nguon=gt.get('nguon') or 'unknown',
                           split=gt.get('split','test'), model=model, rep_pred=s['reps'], rep_true=true_count,
                           abs_error=abs(s['reps']-true_count) if true_count is not None else '',
                           baseline_rep=s['baseline_reps'],
                           baseline_abs_error=abs(s['baseline_reps']-true_count) if true_count is not None else '',
                           plank_pred_s=s['plank_s'], plank_true_s=true_time,
                           plank_abs_error_s=abs(s['plank_s']-true_time) if true_time is not None else '',
                           baseline_plank_abs_error_s=abs(s['baseline_plank_s']-true_time) if true_time is not None else '',
                           form_true=label, form_pred=form_pred, valid_coverage=coverage,
                           frames=result['frames'], processing_seconds=result['processing_seconds'],
                           processing_fps=result['processing_fps'], inference_fps=result['inference_fps'])
                rows.append(row)
                if video in reps_by_video:
                    rep_results.append(dict(video=video, model=model, nguon=row['nguon'], bai=exercise,
                                            **match_reps(reps_by_video[video], result['events'], args.tolerance)))
            except Exception as exc:
                failures.append(dict(video=video, model=model, error=str(exc)))
    metrics = aggregate(rows)
    if rows:
        write_csv(output/'predictions.csv', rows, list(rows[0]))
    write_csv(output/'failures.csv', failures, ['video','model','error'])
    (output/'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    rep_groups = defaultdict(list)
    for r in rep_results:
        rep_groups[(r['model'],r['nguon'],r['bai'])].append(r)
    rep_metrics = []
    for (model, source, exercise), group in rep_groups.items():
        matched, missed, extra = (sum(r[k] for r in group) for k in ('matched','missed','extra'))
        rep_metrics.append(dict(model=model, nguon=source, bai=exercise, matched=matched, missed=missed, extra=extra,
                                detection_precision=matched/(matched+extra) if matched+extra else 0,
                                detection_recall=matched/(matched+missed) if matched+missed else 0,
                                form=form_metrics([pair for r in group for pair in r['pairs']])))
    (output/'rep_metrics.json').write_text(json.dumps(rep_metrics, indent=2), encoding='utf-8')
    (output/'unlabeled_videos.json').write_text(json.dumps(sorted(discovered-{g['video'].replace('\\','/') for g in truth}), indent=2))
    lines = ['# Baseline và bản cải tiến', '', 'Số liệu tính trên video đã gán nhãn. Form là nhãn ở cấp video; xem rep_metrics.json cho cấp rep.', '',
             '| Model | Nguồn | Bài | n | MAE rep | MAE baseline | Đếm đúng | MAE plank (s) | FPS xử lý |',
             '|---|---|---|---:|---:|---:|---:|---:|---:|']
    fmt = lambda v: 'N/A' if v is None else f'{v:.3f}'
    for m in metrics:
        lines.append(f"| {m['model']} | {m['nguon']} | {m['bai']} | {m['videos']} | {fmt(m['count_mae'])} | {fmt(m['baseline_count_mae'])} | {fmt(m['exact_count_rate'])} | {fmt(m['plank_mae_s'])} | {fmt(m['processing_fps'])} |")
    lines.extend(['', f'Video/model lỗi: {len(failures)}. Phải báo cáo số lỗi, không xem là kết quả thành công.',
                  'Baseline squat tái hiện logic starter trên cùng landmarks Tasks; không phải so sánh hai bộ pose detector.',
                  'Baseline push-up/plank là mở rộng. Baseline không chấm form nên F1 form baseline là N/A.',
                  'FPS batch không có HUD/ghi hình; không được gọi là FPS demo webcam.'])
    (output/'comparison.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Bao cao: {output}; {len(rows)} ket qua; {len(failures)} loi')
    if not rows or failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
