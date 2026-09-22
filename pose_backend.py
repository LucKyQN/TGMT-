"""MediaPipe Tasks API, VIDEO mode dong bo cho webcam va file."""
from pathlib import Path
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

ROOT = Path(__file__).resolve().parent
CONNECTIONS = [(11,12),(11,13),(13,15),(12,14),(14,16),(11,23),(12,24),
               (23,24),(23,25),(25,27),(24,26),(26,28),(27,29),(29,31),(27,31),
               (28,30),(30,32),(28,32)]


class PoseBackend:
    def __init__(self, model='full'):
        path = ROOT / 'models' / f'pose_landmarker_{model}.task'
        if not path.is_file():
            raise FileNotFoundError(f'Thieu {path}. Chay: python download_models.py --model {model}')
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(path)),
            running_mode=vision.RunningMode.VIDEO, num_poses=1,
            min_pose_detection_confidence=0.6, min_pose_presence_confidence=0.6,
            min_tracking_confidence=0.6)
        self.detector = vision.PoseLandmarker.create_from_options(options)
        self.last_ms = -1

    def detect(self, frame, seconds):
        timestamp = max(self.last_ms + 1, round(seconds * 1000))
        self.last_ms = timestamp
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp)
        return result.pose_landmarks[0] if result.pose_landmarks else None

    def close(self):
        self.detector.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


def draw_skeleton(frame, landmarks, threshold=0.65):
    if not landmarks:
        return
    h, w = frame.shape[:2]
    points = {i: (round(p.x*w), round(p.y*h)) for i, p in enumerate(landmarks)
              if p.visibility >= threshold and p.presence >= 0.5 and 0 <= p.x <= 1 and 0 <= p.y <= 1}
    for a, b in CONNECTIONS:
        if a in points and b in points:
            cv2.line(frame, points[a], points[b], (88, 222, 174), 3, cv2.LINE_AA)
    for i, point in points.items():
        if i >= 11:
            cv2.circle(frame, point, 5, (255, 238, 211), -1, cv2.LINE_AA)
