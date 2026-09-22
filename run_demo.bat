@echo off
cd /d "%~dp0"
echo Demo se luu raw.mp4, demo.mp4 va CSV vao sessions.
".venv\Scripts\python.exe" 06_pose_estimation.py --model full --record
pause
