"""Kiem tra pipeline tren video TRONG; khong dung lam bang chung accuracy."""
from pathlib import Path
import json
import cv2
import numpy as np
from app import run_capture, hud
from exercise_engine import ExerciseEngine

folder = Path('build/smoke')
folder.mkdir(parents=True, exist_ok=True)
video = folder / 'blank.mp4'
writer = cv2.VideoWriter(str(video), cv2.VideoWriter_fourcc(*'mp4v'), 15, (640,480))
assert writer.isOpened()
for _ in range(16):
    writer.write(np.zeros((480,640,3),np.uint8))
writer.release()
results=[]
for model in ('lite','full','heavy'):
    result=run_capture(str(video),'plank',model,display=False,record=True,output=folder/model)
    assert result['frames']==16
    assert result['segments'][0]['plank_s']==0
    for filename, expected_size in [('demo.mp4',(1280,720)),('raw.mp4',(640,480))]:
        cap=cv2.VideoCapture(str(folder/model/filename))
        ok, frame=cap.read()
        assert ok and (frame.shape[1],frame.shape[0])==expected_size
        assert int(cap.get(cv2.CAP_PROP_FRAME_COUNT))==16
        cap.release()
    results.append(dict(model=model,frames=result['frames'],no_false_plank=True))
engine=ExerciseEngine('squat')
engine.feedback='KIEM TRA GIAO DIEN - CHUA CO VIDEO TAP'
canvas=hud(np.zeros((480,640,3),np.uint8),None,engine,0,0,'full','Chua do accuracy',False)
cv2.imwrite(str(folder/'hud.png'),canvas)
(folder/'checks.json').write_text(json.dumps(results,indent=2))
print('PASS: 3 models; video I/O; timestamps; recording; no-pose case')
