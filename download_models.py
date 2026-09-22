"""Tai model chinh thuc tu Google; khong can tai lai khi demo offline."""
import argparse
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--model', choices=['lite', 'full', 'heavy', 'all'], default='full')
    args = p.parse_args()
    folder = ROOT / 'models'
    folder.mkdir(exist_ok=True)
    for model in ('lite', 'full', 'heavy') if args.model == 'all' else (args.model,):
        url = f'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_{model}/float16/1/pose_landmarker_{model}.task'
        target = folder / f'pose_landmarker_{model}.task'
        if not target.exists():
            temporary = target.with_suffix('.download')
            print(f'Dang tai {model}...', flush=True)
            with urllib.request.urlopen(url, timeout=120) as response, temporary.open('wb') as output:
                while block := response.read(1024 * 1024):
                    output.write(block)
            if not zipfile.is_zipfile(temporary):
                raise RuntimeError(f'Tai model khong hop le: {temporary}')
            temporary.replace(target)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        target.with_suffix('.json').write_text(json.dumps(dict(url=url, sha256=digest), indent=2))
        print(f'{target.name}: {target.stat().st_size / 1e6:.1f} MB | SHA256 {digest}')


if __name__ == '__main__':
    main()
