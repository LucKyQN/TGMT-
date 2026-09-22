"""Nguong thu nghiem, KHONG phai tieu chuan y khoa. Tune tren tap dev."""
from dataclasses import dataclass, field, asdict
import json
import math
from pathlib import Path


@dataclass
class SquatConfig:
    up: float = 160.0
    start: float = 145.0
    down: float = 100.0
    max_lean: float = 55.0


@dataclass
class PushupConfig:
    up: float = 160.0
    start: float = 145.0
    down: float = 90.0
    min_body: float = 160.0
    max_horizontal: float = 35.0


@dataclass
class PlankConfig:
    min_body: float = 160.0
    max_horizontal: float = 25.0
    confirm_seconds: float = 0.30
    confirm_frames: int = 4


@dataclass
class Config:
    squat: SquatConfig = field(default_factory=SquatConfig)
    pushup: PushupConfig = field(default_factory=PushupConfig)
    plank: PlankConfig = field(default_factory=PlankConfig)
    visibility: float = 0.65
    presence: float = 0.5
    ema_seconds: float = 0.10
    transition_seconds: float = 0.15
    max_gap_seconds: float = 0.50
    min_rep_seconds: float = 0.40
    max_rep_seconds: float = 20.0
    video_form_fraction: float = 0.90

    def validate(self):
        values = asdict(self)
        numbers = [n for v in values.values() for n in (v.values() if isinstance(v, dict) else [v])]
        if not all(isinstance(v, (float, int)) and math.isfinite(v) for v in numbers):
            raise ValueError('Tat ca nguong phai la so huu han')
        for c in (self.squat, self.pushup):
            if not 0 < c.down < c.start < c.up < 180:
                raise ValueError('Can 0 < down < start < up < 180')
        if not 0 <= self.visibility <= 1 or not 0 <= self.presence <= 1:
            raise ValueError('visibility/presence phai trong [0,1]')
        if min(self.ema_seconds, self.transition_seconds, self.max_gap_seconds,
               self.min_rep_seconds, self.plank.confirm_seconds) <= 0:
            raise ValueError('Thoi gian phai duong')
        if self.max_rep_seconds <= self.min_rep_seconds or self.plank.confirm_frames < 2:
            raise ValueError('Gioi han rep/frame khong hop le')
        if not 0 < self.video_form_fraction <= 1:
            raise ValueError('video_form_fraction phai trong (0,1]')
        if not 0 < self.squat.max_lean < 90:
            raise ValueError('max_lean phai trong (0,90)')
        for c in (self.pushup, self.plank):
            if not 0 < c.min_body < 180 or not 0 < c.max_horizontal < 90:
                raise ValueError('Nguong than khong hop le')
        return self


def load_config(path=None):
    cfg = Config()
    if path:
        data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        for key, value in data.items():
            if not hasattr(cfg, key):
                raise ValueError(f'Cau hinh khong ton tai: {key}')
            if key in ('squat', 'pushup', 'plank'):
                value = type(getattr(cfg, key))(**value)
            setattr(cfg, key, value)
    return cfg.validate()


if __name__ == '__main__':
    print(json.dumps(asdict(Config()), indent=2))
