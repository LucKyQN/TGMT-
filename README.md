# IUH Motion Lab — Chủ đề 6

Ứng dụng Python phân tích **squat, hít đất, plank**, webcam hoặc video, góc quay bên hông. MediaPipe Tasks PoseLandmarker + OpenCV + NumPy. Code phân tích và đánh giá được viết riêng cho đồ án; repo ngoài chỉ là tài liệu tham khảo.

**Trạng thái:** đã kiểm tra camera laptop, khởi tạo cả 3 model, đọc/ghi video và kiểm thử logic. Chưa có tập video tập luyện được gán nhãn nên **chưa có kết luận về accuracy**. Ngưỡng hiện tại là giả thuyết cần tune. Bộ slide HTML 12 trang là bản trình bày phương pháp, còn bảng kết quả cần dữ liệu thật.

**Chưa train thêm mô hình trên dataset nào.** MediaPipe cung cấp pose model đã huấn luyện sẵn; phần đúng/sai hiện dựa trên luật góc do nhóm cấu hình. Kaggle Real-Time Exercise Recognition và Yoga Poses mới được khảo sát, chưa tải toàn bộ hoặc gán nhãn để đánh giá. Xem [ghi chú quá trình làm](docs/DEVELOPMENT_LOG.md) và [nguồn tham khảo](docs/RESEARCH.md).

## 1. Chạy `main()` hoàn chỉnh

Windows / Python **3.11** / VS Code. Trong thư mục dự án:

```powershell
git clone https://github.com/LucKyQN/TGMT-.git
cd TGMT-
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe download_models.py --model all
.\.venv\Scripts\python.exe 06_pose_estimation.py --source 0 --exercise squat --model full
```

Repo không chứa `.venv`, file model `.task` hoặc video cá nhân. Trên máy mới, thực hiện đầy đủ các lệnh trên; cần Internet khi cài thư viện và tải model. Nếu máy đã có môi trường và model thì không cần cài lại. VS Code: `Python: Select Interpreter` → `.venv\Scripts\python.exe`. Dùng đường dẫn Python trực tiếp nên không gặp lỗi ExecutionPolicy khi activate.

Có thể mở `run_camera.bat` để tập không ghi hình hoặc `run_demo.bat` để **ghi hình**.

```powershell
# Ghi video gốc, video có HUD và CSV
.\.venv\Scripts\python.exe 06_pose_estimation.py --record
# Hít đất bằng video
.\.venv\Scripts\python.exe 06_pose_estimation.py --source data/videos/pushup_01.mp4 --exercise pushup --record
# Plank, model nhẹ
.\.venv\Scripts\python.exe 06_pose_estimation.py --exercise plank --model lite
```

Phím **1 / 2 / 3**: squat / push-up / plank, tạo phân đoạn mới và reset bộ đếm. Lịch sử phân đoạn cũ vẫn được lưu. **Q**: thoát, hoàn tất file. Cửa sổ đóng bằng X cũng kết thúc.

### Đặt camera

- Đặt laptop cố định, ống kính gần ngang hông; người tập quay ngang, thấy vai đến mắt cá. Tránh để chân/cổ tay ra ngoài ảnh.
- Squat cần nhìn rõ vai–hông–gối–mắt cá. Hít đất cần thêm khuỷu tay và cổ tay. Di chuyển camera thấp hơn khi tập sát sàn.
- Bắt đầu squat ở tư thế đứng, hít đất ở tư thế chống tay lên. Giữ khoảng 1 giây trước rep đầu.
- Chọn đúng bài bằng phím: ứng dụng **không tự phân loại bài tập**. Chỉ một người trong khung hình.
- Cảnh báo `MAT DAU` có nghĩa chưa đủ thông tin, không phải kết luận người tập sai.

### File kết quả mỗi lần chạy

`sessions/<ngày_giờ>/` chứa:

| File | Nội dung |
|---|---|
| `frames.csv` | Timestamp, góc thô/góc lọc, bên, trạng thái, valid, bộ đếm |
| `reps.csv` | Mỗi rep: thời điểm, góc nhỏ nhất, thân, nhãn và lý do |
| `sessions.csv` | Tổng kết từng phân đoạn/bài; thời gian plank |
| `summary.json` | Cấu hình, model, FPS, số frame, kết quả và lỗi nếu có |
| `raw.mp4` | Video trước khi vẽ, chỉ khi dùng `--record` |
| `demo.mp4` | Video có skeleton và HUD, chỉ khi dùng `--record` |

Video webcam được ghi CFR 20 FPS bằng lấy mẫu theo timestamp; có thể lặp/bỏ khung hình để giữ thời lượng. `raw.mp4` không có âm thanh và không bảo toàn mọi frame camera gốc. Dùng cùng file này khi gán nhãn và chạy batch để đối chiếu công bằng. `frames.csv` giữ timestamp thực của xử lý live; batch có thể khác nhẹ do lấy mẫu lại.

## 2. Đánh giá batch

Đặt video vào `data/videos/`. Quét thư mục (kể cả thư mục con):

```powershell
.\.venv\Scripts\python.exe make_manifest.py --output data/to_label.csv
```

**Điền nhãn bằng quan sát**, rồi lưu thành `data/ground_truth.csv`. Mẫu ví dụ dưới đây chỉ giải thích định dạng, không phải kết quả đã đo:

```csv
video,bai,so_rep_that,form,ghi_chu,nguon,split,subject,plank_giay_that,fps
tu_quay/squat_01.mp4,squat,5,dung,toan bo rep dat,tu_quay,dev,P01,,
tu_quay/pushup_01.mp4,pushup,4,mixed,co rep sai,tu_quay,test,P02,,
tu_quay/plank_01.mp4,plank,0,sai,co doan hong vong,tu_quay,test,P02,12.4,
```

- `bai`: `squat`, `pushup`, `plank`.
- `nguon`: `tu_quay`, `realtime_real`, `realtime_synthetic`; không xác minh được thì `unknown`.
- `split`: `dev` để tune, `test` để báo cáo. Tách theo người/buổi hoặc video nguồn; không chia các đoạn cùng video vào hai tập.
- `so_rep_that`: **mọi chu kỳ hoàn thành**, gồm cả rep nông/sai. Plank để 0.
- `form` cấp video: squat/push-up `dung` nếu tất cả rep đúng; `sai` nếu video có lỗi theo quy ước; `mixed` để bỏ qua F1 cấp video và dùng nhãn từng rep.
- Plank: cắt clip vào khoảng đang thực hiện; `dung` nếu ít nhất 90% thời lượng clip có form đạt theo quan sát, còn lại `sai`. Không tính đoạn chuẩn bị dài vào clip.
- `plank_giay_that`: tổng thời gian các khoảng plank đúng do người quan sát bấm giờ, bắt buộc cho plank. Không dùng tổng độ dài video thay thế.
- `fps`: chỉ điền nếu biết FPS metadata sai. Video VFR nên chuyển sang CFR trước khi gán nhãn vì bài dùng `frame_idx/fps`.

Nhãn từng rep, `data/rep_ground_truth.csv`:

```csv
video,rep,end_s,form
tu_quay/pushup_01.mp4,1,2.30,dung
tu_quay/pushup_01.mp4,2,4.65,sai
```

Điền **đủ mọi rep** của video được chọn; số hàng phải bằng `so_rep_that`. `end_s` là lúc trở về tư thế lên, lấy theo timeline file, không theo đồng hồ lúc mở video.

```powershell
.\.venv\Scripts\python.exe evaluate.py --videos data/videos --ground-truth data/ground_truth.csv --rep-truth data/rep_ground_truth.csv --models lite full heavy --split test
```

Script duyệt video được khai báo trong manifest, đồng thời liệt kê video chưa gán nhãn. Kết quả trong `evaluation/<ngày_giờ>/`:

- `predictions.csv`: từng video/model, đếm dự đoán/thật, sai số, form dự đoán/thật, FPS.
- `metrics.json`: MAE, tỉ lệ đếm đúng hoàn toàn, confusion matrix 2×3 (`dung/sai/unknown`), precision/recall/F1 từng lớp, coverage, sai số plank; tách nguồn và bài.
- `rep_metrics.json`: ghép rep theo thời điểm với dung sai mặc định 0.75 s; rep bỏ sót là `unknown` khi tính recall, rep dư phản ánh ở detection precision.
- `comparison.md`: bảng baseline–cải tiến. `failures.csv`: lỗi cần xử lý; batch trả exit code 1 nếu có lỗi hoặc không có kết quả.
- `unlabeled_videos.json`: video có trong thư mục nhưng chưa được khai báo.

Không bỏ các ca khó/lỗi rồi chỉ báo accuracy của ca tốt. Báo số video lỗi, số nhãn có thể chấm, coverage và số mẫu từng lớp. Macro-F1 dùng cả hai lớp; nếu một lớp không có mẫu thì phải nêu rõ và bổ sung dữ liệu.

**Baseline:** squat giữ đúng logic starter: chân trái, góc normalized, không lọc visibility/EMA, đếm khi xuống <100° sau khi lên >160°. Cùng landmarks Tasks để so sánh phần hậu xử lý. Hít đất/plank là baseline mở rộng, phải ghi rõ; baseline không dự đoán form nên F1 baseline = N/A. Muốn so sánh cả detector legacy với Tasks cần một thí nghiệm khác.

**FPS:** `inference_fps` chỉ đo lời gọi pose; `processing_fps` batch bao gồm đọc video, đo và ghi CSV, không HUD/ghi hình. FPS live có HUD phải đo riêng trong buổi demo. 30 frame smoke test không phải benchmark ổn định.

## 3. Thư viện, model, cấu hình

`requirements.txt` pin ba thư viện chính; dùng `requirements-lock.txt` để tái tạo đầy đủ môi trường đã kiểm tra. `opencv-contrib-python` là bản OpenCV có `cv2`; không cài đồng thời `opencv-python` hoặc bản headless trong venv này.

Model chính thức được `download_models.py` tải từ Google, phiên bản đường dẫn `float16/1`. Các file `.json` đi kèm lưu URL và SHA-256. Sau khi tải, ứng dụng chạy offline:

- [Lite .task](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task)
- [Full .task](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task)
- [Heavy .task](https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_heavy/float16/1/pose_landmarker_heavy.task)
- [MediaPipe Pose Landmarker Python](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python)

Sửa bản sao `config.example.json`, rồi truyền `--config config.example.json` cho **cả demo và batch**. Giữ nguyên file config đã chốt khi chạy test. Các dataclass trong `config.py` tách ngưỡng khỏi logic.

## Đọc code theo thứ tự

1. `config.py`: giả thuyết và các ngưỡng từng bài.
2. `exercise_engine.py`: tích vô hướng, pixel, visibility, EMA, state machine, baseline.
3. `pose_backend.py`: khởi tạo `.task`, BGR→RGB, timestamp, tự vẽ skeleton.
4. `app.py`: `main()` hoàn chỉnh, vòng đọc hình, gọi phân tích, HUD, CSV và ghi video.
5. `evaluate.py`: ground truth → dự đoán → sai số, confusion matrix và bảng so sánh.

Chạy kiểm thử:

```powershell
.\.venv\Scripts\python.exe -m unittest test_exercises -v
.\.venv\Scripts\python.exe smoke_check.py
```

Smoke test tạo **video đen**, chỉ xác nhận I/O và trường hợp không có người. Không dùng nó làm video demo hoặc số liệu accuracy của đồ án.

## Tài liệu đồ án

- [Báo cáo phương pháp](docs/REPORT.md): công thức, logic, thiết kế thực nghiệm, hạn chế và hướng mở rộng.
- [Nguồn tham khảo](docs/RESEARCH.md): repo GitHub, nguồn dataset và mức phù hợp.
- [Demo và bảo vệ](docs/DEMO_AND_DEFENSE.md): kịch bản demo, kế hoạch 30 video, câu hỏi bảo vệ.
- [Nhật ký phát triển](docs/DEVELOPMENT_LOG.md): các bước đã làm, quyết định và việc còn lại.
- [Slide HTML](slides/index.html): 12 slide offline; tải/clone repo rồi mở file bằng trình duyệt, phím mũi tên, F11 toàn màn hình, N mở ghi chú. Đây chưa phải file PowerPoint.

Nếu camera không mở: đóng Teams/Zoom/ứng dụng Camera; bật quyền camera cho desktop apps trong Windows; thử `--source 1`. Nếu thấy người nhưng `MAT DAU`, lùi xa/đổi góc để thấy đủ chân và tay. Nếu chậm, dùng lite. Không hạ visibility chỉ để hết cảnh báo mà chưa kiểm tra độ tin cậy.
