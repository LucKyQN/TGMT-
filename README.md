# Motion Lab — Phân tích động tác thể thao

Ứng dụng Python sử dụng **MediaPipe Pose, OpenCV và NumPy** để phân tích tư thế từ webcam hoặc video.

## Chức năng

- **Squat, hít đất:** đếm lần lặp hoàn thành và đánh giá theo góc khớp.
- **Plank:** đo thời gian giữ tư thế đạt tiêu chí.
- Hiển thị khung xương, góc khớp, trạng thái và FPS.
- Ghi video demo, lưu kết quả CSV và đánh giá với nhãn thủ công.

Ứng dụng dùng model MediaPipe có sẵn, chưa huấn luyện thêm. Đánh giá đúng/sai hiện dựa trên ngưỡng góc thử nghiệm; chưa có kết quả độ chính xác trên tập video được gán nhãn.

## Cài đặt

Yêu cầu: **Python 3.11**, Windows và webcam nếu muốn chạy trực tiếp.

```powershell
git clone https://github.com/LucKyQN/TGMT-.git
cd TGMT-
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe download_models.py --model full
```

Cần Internet để cài thư viện và tải model lần đầu. Sau đó có thể chạy offline.

## Sử dụng

Chạy webcam và ghi demo:

```powershell
.\.venv\Scripts\python.exe 06_pose_estimation.py --record
```

Chạy video có sẵn:

```powershell
.\.venv\Scripts\python.exe 06_pose_estimation.py --source "video.mp4" --exercise pushup
```

- Phím **1 / 2 / 3**: chọn squat / hít đất / plank, reset bộ đếm của bài đang chọn.
- Phím **Q**: thoát và lưu kết quả.
- Đặt camera **bên hông**, nhìn rõ toàn thân và các khớp tay/chân.
- Kết quả nằm trong `sessions/`. Thêm `--record` để lưu video gốc và video có phân tích.

Có thể mở `run_camera.bat` hoặc `run_demo.bat` sau khi cài đặt. Ngưỡng nằm trong `config.py`; dùng `--config config.example.json` để nạp cấu hình riêng. Hỗ trợ model `lite`, `full`, `heavy` qua tùy chọn `--model` sau khi tải model tương ứng.

## Đánh giá và kiểm thử

Đặt video vào `data/videos/`, điền nhãn quan sát vào `data/ground_truth.csv`, rồi chạy:

```powershell
.\.venv\Scripts\python.exe evaluate.py --models full --split test
.\.venv\Scripts\python.exe -m unittest test_exercises -v
```

Kết quả đánh giá nằm trong `evaluation/`, gồm sai số đếm, chỉ số đánh giá tư thế và bảng so sánh baseline. Xem quy ước nhãn và phương pháp trong tài liệu bên dưới.

## Tài liệu

- [Quá trình thực hiện và việc còn lại](docs/DEVELOPMENT_LOG.md)
- [Công thức, thuật toán và đánh giá](docs/REPORT.md)
- [Repo tham khảo và dataset](docs/RESEARCH.md)
- [Kịch bản demo và bảo vệ](docs/DEMO_AND_DEFENSE.md)
- [Slide HTML](slides/index.html) — mở bằng trình duyệt sau khi tải repo.
