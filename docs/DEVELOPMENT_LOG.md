# Ghi chú quá trình làm đồ án

## Ngày 22/09/2026 — Bản triển khai đầu tiên

### 1. Tiếp nhận đề và xác định phạm vi

- Đề ban đầu cung cấp starter đếm squat bằng góc gối, ngưỡng lên/xuống 160°/100°, chỉ dùng chân trái.
- Bắt đầu xây dựng bản squat cho camera laptop, sau đó mở rộng phạm vi theo yêu cầu thành squat, hít đất và plank.
- Chốt chạy local trên Windows, Python 3.11, VS Code và venv. Camera bên hông, một người trong khung hình.

### 2. Chuẩn bị môi trường

- Tạo `.venv` riêng vì môi trường Python dùng chung có các phiên bản thư viện dễ xung đột.
- Pin MediaPipe 0.10.21, OpenCV contrib 4.11.0.86, NumPy 1.26.4; lưu toàn bộ phiên bản trong `requirements-lock.txt`.
- Chuyển từ hướng API `mp.solutions.pose` của starter sang **MediaPipe Tasks PoseLandmarker** theo yêu cầu đã chốt.
- Thêm script tải model lite/full/heavy chính thức, lưu URL và SHA-256. Model được tải trên máy phát triển nhưng không đưa file nhị phân vào Git.

### 3. Xây dựng thuật toán

- Tính góc bằng arccos tích vô hướng, chuyển tọa độ normalized sang pixel; xử lý vector suy biến và sai số miền arccos.
- Chọn trái/phải theo visibility, kiểm tra presence/vị trí trong ảnh; hạn chế đổi bên liên tục.
- Làm mượt bằng EMA theo thời gian; chuyển trạng thái có ngưỡng tách biệt và thời gian xác nhận.
- Đếm khi trở lại tư thế lên. Thêm ngưỡng bắt đầu hạ để rep nông vẫn có thể được đếm và gắn nhãn sai.
- Chấm cực trị góc trên cả rep; mất dấu hoặc đổi bên sẽ hủy rep đang dở.
- Plank cần thân thẳng và gần nằm ngang; chỉ cộng thời gian khi trạng thái HOLD đã được xác nhận.
- Video dùng `frame_idx / FPS`; webcam dùng `perf_counter()`.

### 4. Xây dựng ứng dụng và đánh giá

- HUD 1280×720, skeleton tự vẽ, chữ không dấu, góc, trạng thái, rep đúng/sai, thời gian plank và FPS.
- Phím 1/2/3 đổi bài và reset phân đoạn; Q kết thúc. CSV lưu từng frame, từng rep và từng phân đoạn.
- Tùy chọn `--record` lưu video gốc và video có HUD, lấy mẫu theo timestamp để giữ thời lượng.
- Tạo script batch đọc manifest, tách nguồn/người/split, so baseline và bản cải tiến, xuất bảng và chỉ số.
- Thêm nhãn từng rep vì một nhãn video không đủ khi clip có cả rep đúng và sai; matching theo thời điểm kết thúc.
- Giữ `unknown` trong đánh giá để không che giấu thiếu quan sát. Baseline không có form nên không tạo F1 baseline giả.

### 5. Khảo sát tài liệu và dataset

- Tìm repo cùng ý tưởng; liên kết và phạm vi tham khảo được ghi tại [RESEARCH.md](RESEARCH.md).
- Xác minh mô tả công khai của Real-Time Exercise Recognition Dataset và Yoga Poses Dataset.
- Phân biệt video thật/avatar; phân biệt nhãn loại bài với nhãn chất lượng động tác.
- **Chưa tải toàn bộ dataset, chưa gán nhãn video tập, chưa train thêm model.**

### 6. Kiểm tra đã thực hiện

| Kiểm tra | Kết quả | Giới hạn bằng chứng |
|---|---|---|
| `pip check` | Không phát hiện dependency bị lỗi | Không chứng minh thuật toán đúng |
| Unit test | 19 kiểm thử đạt | Dữ liệu góc/landmark giả lập có kiểm soát |
| Camera laptop + lite | Đọc và xử lý 30 frame | Không có buổi tập được gán nhãn; không đo accuracy |
| Smoke test lite/full/heavy | Đọc/ghi video và ca không có người hoạt động | Video trống, không phải video demo tập |
| Batch qua 3 model | 3 kết quả, 0 lỗi xử lý | Fixture video trống, không dùng làm số liệu đồ án |
| HUD | Đã xem ảnh kiểm tra bố cục | Cần kiểm tra tiếp trên máy chiếu |

Các test và báo cáo smoke nằm ở máy phát triển trong `build/` và không được commit. Có thể chạy lại bằng hướng dẫn README. Slide HTML đã được soạn 12 trang; chưa có bản PPTX và chưa xác nhận hiển thị toàn bộ slide trên máy chiếu.

### 7. Làm rõ cơ sở đúng/sai

Sau câu hỏi về dữ liệu train, đã xác nhận rõ: MediaPipe chỉ cung cấp khớp; lớp chấm form hiện là **rule-based**. Các ngưỡng là giá trị thử nghiệm, chưa được kiểm chứng bằng dữ liệu của nhóm. Không gọi unit-test pass hoặc tỉ lệ phát hiện người là độ chính xác chấm tư thế.

### 8. Chuẩn bị đưa lên GitHub

- Thêm hướng dẫn clone, cài môi trường, tải model, chạy camera/video, ghi demo, gán nhãn và đánh giá.
- Loại `.venv`, model nhị phân, video, session camera, output đánh giá và file tạm khỏi Git.
- Repo chứa mã nguồn, test, cấu hình, mẫu CSV chỉ có tiêu đề và tài liệu phương pháp.

## Công việc tiếp theo

- [ ] Chọn nguồn chuyên môn cho tiêu chí kỹ thuật và nêu rõ giới hạn đo được bằng góc 2D.
- [ ] Thu video tự quay dự kiến 10 clip/bài, có người/buổi và ca khó đa dạng.
- [ ] Gán nhãn thủ công độc lập; kiểm tra bất đồng giữa người gán nhãn.
- [ ] Chọn video bên hông từ dataset bổ sung; tách nguồn thật và tổng hợp.
- [ ] Tune trên dev, cố định config rồi chạy test riêng.
- [ ] Báo MAE, tỉ lệ đếm đúng, F1, coverage, sai số plank và FPS; phân tích các ca thất bại.
- [ ] Quay demo tập thật và đối chiếu CSV/nhãn.
- [ ] Cập nhật báo cáo và slide bằng số liệu thực; hoàn thiện định dạng nộp theo yêu cầu giảng viên.

## Quy ước cập nhật nhật ký

Mỗi lần cập nhật ghi ngày, thay đổi, lý do, cách kiểm tra và việc còn lại. Khi đổi ngưỡng, ghi tập dev dùng để quyết định; không điều chỉnh dựa trên tập test rồi báo đó là kết quả độc lập. Mọi số liệu phải truy được về video, nhãn, config và model.
