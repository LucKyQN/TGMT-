"""Quet video va tao CSV rong de NGUOI gan nhan. Khong sinh nhan gia."""
import argparse
from pathlib import Path
from app import write_csv

p = argparse.ArgumentParser()
p.add_argument('--videos', type=Path, default=Path('data/videos'))
p.add_argument('--output', type=Path, default=Path('data/to_label.csv'))
a = p.parse_args()
fields = ['video','bai','so_rep_that','form','ghi_chu','nguon','split','subject','plank_giay_that','fps']
if a.output.exists():
    p.error('File da ton tai, chon --output moi de khong mat nhan')
rows = []
for path in sorted(a.videos.rglob('*')):
    if path.suffix.lower() in ('.mp4','.avi','.mov','.mkv'):
        rows.append(dict(video=path.relative_to(a.videos).as_posix()))
a.output.parent.mkdir(parents=True, exist_ok=True)
write_csv(a.output, rows, fields)
print(f'{len(rows)} video -> {a.output}')
