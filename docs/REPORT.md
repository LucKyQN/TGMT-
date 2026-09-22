# Báo cáo phương pháp — Ước lượng tư thế người và phân tích động tác thể thao

**Môn:** Thị giác máy tính, IUH · **Chủ đề:** 6  
**Phiên bản:** triển khai và thiết kế thực nghiệm; chưa có kết quả đánh giá trên người tập được gán nhãn.

## 1. Bài toán và phạm vi

Đầu vào là webcam hoặc video một người tập, camera cố định nhìn từ bên hông. Người dùng chọn squat, hít đất hoặc plank. Đầu ra gồm skeleton, góc khớp, trạng thái, số rep hoàn thành/đạt/chưa đạt, thời gian plank đúng, cảnh báo và lịch sử CSV.

MediaPipe sử dụng mô hình đã huấn luyện để phát hiện pose. Nhóm xây dựng lớp phân tích hình học và trạng thái; không huấn luyện mạng mới. “Đúng/sai” trong sản phẩm là **đạt/chưa đạt bộ tiêu chí quan sát đã định nghĩa**, không phải chứng nhận kỹ thuật toàn diện.

## 2. Kiến trúc

`VideoCapture → PoseLandmarker → kiểm tra khớp → tọa độ pixel → góc → EMA → máy trạng thái → phản hồi + CSV + video`

Model lite/full/heavy được chọn lúc chạy. `PoseBackend` dùng MediaPipe Tasks ở chế độ VIDEO đồng bộ cho cả webcam và file: mỗi frame được xử lý, dễ gắn kết quả với timestamp và kiểm thử. Đây là chế độ xử lý tuần tự, không phải callback LIVE_STREAM bất đồng bộ. [Tài liệu API](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python).

Việc chọn chế độ VIDEO không có nghĩa webcam không chạy thời gian thực: thời gian thực phải được đánh giá bằng FPS và độ trễ thực trên máy. Có thể đổi sang LIVE_STREAM để tăng khả năng đáp ứng, nhưng phải xử lý frame bị bỏ và callback cẩn thận.

## 3. Công thức góc

Landmark ảnh được chuẩn hóa riêng theo chiều rộng và chiều cao. Chuyển:

\[
A=(x_AW,y_AH),\quad B=(x_BW,y_BH),\quad C=(x_CW,y_CH)
\]

Với \(u=A-B\), \(v=C-B\):

\[
\theta=\arccos\left(\operatorname{clip}\left(\frac{u\cdot v}{\|u\|\|v\|},-1,1\right)\right)\frac{180}{\pi}
\]

`calculate_angle()` trả `None` nếu vector gần bằng 0. `clip` bảo vệ miền xác định của arccos trước sai số số thực. Pixel sửa sự méo do chuẩn hóa không đồng nhất; **không sửa được phối cảnh hoặc xoay người ra khỏi mặt phẳng ảnh**.

Các góc sử dụng:

| Đại lượng | Điểm/vector |
|---|---|
| Góc gối squat | hông–gối–mắt cá |
| Góc khuỷu hít đất | vai–khuỷu–cổ tay |
| Góc đường thân | vai–hông–mắt cá |
| Nghiêng thân so với dọc | vector hông→vai và vector hướng lên `(0,-1)` |
| Lệch ngang | `atan2(abs(dy), abs(dx))` của vector hông→vai |

Góc đường thân không đo độ cong cột sống. Nghiêng thân trong squat có thể thay đổi theo cơ thể và biến thể bài; ngưỡng 55° chỉ là tiêu chí thử nghiệm.

## 4. Chọn bên và làm mượt

Mỗi bài có danh sách khớp bắt buộc. Chỉ xét bên có toàn bộ khớp trong ảnh, visibility ≥0.65 và presence ≥0.5. Chọn bên có tổng visibility lớn nhất; giữ bên trước nếu chênh lệch dưới 0.3 để giảm nhảy qua lại. Khi đổi bên hoặc mất khớp, hủy chu kỳ đang dở, giữ số rep đã hoàn thành.

EMA theo thời gian:

\[
\alpha=1-e^{-\Delta t/\tau},\qquad \bar\theta_t=\bar\theta_{t-1}+\alpha(\theta_t-\bar\theta_{t-1}),\quad \tau=0.10s
\]

Sử dụng Δt giúp hành vi ít phụ thuộc FPS hơn hệ số cố định. EMA giảm nhiễu nhưng gây trễ và có thể làm mất cực trị rất ngắn. Vì vậy ngưỡng phải tune sau khi bật EMA, không dùng ngưỡng của tín hiệu thô một cách máy móc.

## 5. Máy trạng thái đếm rep

`WAIT_UP → UP → DESCENDING → DOWN → RETURNING → UP`

- Phải xác nhận tư thế lên trước rep đầu.
- `up >160°`, bắt đầu chu kỳ khi góc `<145°`; điều kiện chuyển phải giữ ít nhất 0.15 s.
- Squat đạt độ sâu nếu góc nhỏ nhất `<100°`; hít đất `<90°`.
- Về `UP` mới đếm. Rep quá ngắn dưới 0.4 s hoặc quá lâu trên 20 s bị loại/reset.
- Khoảng mất xử lý >0.5 s hủy chu kỳ đang dở.

**Tại sao có ngưỡng start 145°?** Nếu chỉ bắt đầu rep khi góc <100° rồi mới chấm “đủ sâu”, tất cả rep được đếm đều mặc nhiên đạt độ sâu. Start 145° cho phép theo dõi một chu kỳ nông rồi kết luận `SHALLOW` khi người tập đứng lên. Không qua `DOWN` vẫn có thể hoàn thành một rep chưa đạt. Các co gối rất nhỏ không qua 145° nằm ngoài định nghĩa rep hiện tại và cần phản ánh khi gán nhãn.

Đánh giá tích lũy cả chu kỳ:

- Squat: min(góc gối) <100° **và** max(nghiêng thân) ≤55°.
- Hít đất: min(góc khuỷu) <90° **và** min(góc đường thân) >160°.
- Hít đất yêu cầu thân lệch ngang ≤35° để tránh đếm gập tay khi đứng.

`min_angle`, `min_body`, `max_lean` là cực trị của **góc đã lọc**, không phải phép đo giải phẫu chuẩn. Lỗi thoáng qua có thể ảnh hưởng nhãn cả rep; cần xem log và nghiên cứu yêu cầu lỗi kéo dài nếu dữ liệu cho thấy nhiều báo sai.

## 6. Plank

Điều kiện: góc vai–hông–mắt cá >160° và thân lệch ngang <25°. Cả góc thô và góc EMA phải đạt; gate góc thô giúp dừng đồng hồ ngay khi thấy sai. Tư thế phải ổn định ít nhất 0.30 s và 4 frame, sau đó chỉ cộng Δt giữa hai frame `HOLD` liên tiếp. Không tính ngược thời gian xác nhận.

Không cộng khoảng mất dấu, khoảng sai, thời gian đứng thẳng hoặc thời gian xử lý chờ. Bộ đếm tích lũy các đoạn đúng. Do bỏ thời gian xác nhận, hệ thống có xu hướng thiếu khoảng 0.3 s cộng tối đa một khoảng lấy mẫu ở mỗi đoạn; cần báo sai số này khi đối chiếu người bấm giờ, không chỉnh nhãn thủ công để che sai lệch.

Một người nằm thẳng có thể thỏa hai điều kiện hình học. Phiên bản hiện tại giả định người dùng đã chọn đúng bài và đang ở tư thế chống plank. Kiểm tra tiếp xúc tay/chân và phân biệt nằm nghỉ là hướng bổ sung, không được tuyên bố đã giải quyết.

## 7. Thời gian, video và hiệu năng

- File: \(t_i=i/FPS\), dùng cho cả rep và plank; tốc độ máy không đổi thời gian tập.
- Webcam: `perf_counter()` từ frame đầu, đồng hồ đơn điệu.
- Timestamp đưa vào Tasks là mili giây tăng nghiêm ngặt. Tính plank vẫn sử dụng giây của nguồn, không dùng timestamp đã làm tròn.
- Video demo có FPS cố định, resample theo thời điểm để không tăng tốc khi inference chậm.
- Báo FPS xử lý live riêng với FPS inference và batch. Không suy ra “heavy chính xác hơn” chỉ từ tên model.

## 8. Dữ liệu và ground truth

Video tự quay là dữ liệu chính, dự kiến 10 clip/bài, có trường hợp đúng, sai, thay đổi tốc độ, che khuất. Cần nhiều người/buổi nếu có thể. Thống nhất tiêu chí trước khi gán nhãn; hai người quan sát độc lập một phần hoặc toàn bộ, thảo luận bất đồng và ghi quy tắc.

Nguồn bổ sung: Real-Time Exercise Recognition Dataset cho squat/push-up, tách người thật/avatar; Yoga Poses cho ảnh plank, không dùng đo thời gian. Chi tiết, giấy phép và liên kết trong `RESEARCH.md`.

Mỗi video có tổng rep, form cấp video, nguồn, người tập, split; plank có tổng giây đúng. Với video mixed, bổ sung thời điểm kết thúc và nhãn từng rep. Cố định ngưỡng bằng tập dev trước khi chạy test. Không dùng cùng người/video nguồn ở cả dev và test nếu muốn đánh giá tổng quát hóa.

## 9. Chỉ số và baseline

\[
MAE=\frac{1}{N}\sum_{i=1}^{N}|\hat n_i-n_i|,\qquad Exact=\frac{\sum_i[\hat n_i=n_i]}{N}
\]

\[
Precision=\frac{TP}{TP+FP},\quad Recall=\frac{TP}{TP+FN},\quad F1=\frac{2PR}{P+R}
\]

Plank: MAE giữa số giây dự đoán và quan sát. Form: báo cả hai lớp, support, confusion matrix; `unknown` là cột riêng và là bỏ sót cho lớp thật khi tính recall. Rep được ghép 1–1 theo thời điểm kết thúc trong dung sai 0.75 s, tối đa số cặp rồi tối thiểu lệch thời điểm; báo thêm rep dư và thiếu.

Baseline squat: logic starter chạy trên cùng landmarks Tasks, dùng tọa độ normalized của chân trái, không EMA/visibility, đếm ngay ở đáy. Đây là đối chiếu **logic hậu xử lý**, không phải benchmark OpenPose hay so sánh detector Tasks/legacy. Hít đất/plank là baseline mở rộng có ghi chú. Baseline không có chấm form nên không gán F1 giả.

Kết quả cần báo theo `model × nguồn × bài`; giữ điều kiện phần cứng, độ phân giải và video giống nhau. Nếu benchmark nhiều lần, báo trung bình và biến thiên, không chỉ chọn lần tốt nhất.

## 10. Trạng thái kết quả

| Nội dung | Trạng thái |
|---|---|
| Camera laptop + lite | Đã đọc và xử lý 30 frame; không phải bài tập đã gán nhãn |
| Lite/full/heavy + file/ghi video | Đã kiểm tra bằng video trống, không phải accuracy |
| Công thức, rep, mất dấu, plank, matching | Kiểm thử tự động trong `test_exercises.py` |
| Accuracy, MAE, F1 trên video người tập | **Chưa đo** |
| Video demo tập thật có đối chiếu | **Cần quay và gán nhãn** |

Không lấy tỉ lệ phát hiện người làm độ chính xác chấm tư thế. Chưa có dữ liệu đủ để kết luận bản cải tiến tốt hơn baseline.

## 11. Hạn chế và mở rộng

Góc 2D nhạy với góc quay, phối cảnh, quần áo, ánh sáng và che khuất. Visibility không phải xác suất góc đúng. Không phát hiện chắc chắn gối lệch vào trong từ một góc bên hông; không đo độ cong lưng bằng ba khớp lớn. Ngưỡng cố định có thể không phù hợp mọi người và mọi biến thể bài.

Vật lý trị liệu: trước hết cần hiệu chỉnh cá nhân, đo ROM và độ lặp lại so với dụng cụ/chuyên gia; xây dựng tiêu chí bài riêng, kiểm định trên đối tượng phù hợp. Hiện chưa xác nhận sử dụng lâm sàng. Huấn luyện chuyên sâu: thêm nhịp eccentric/concentric, độ đối xứng, tốc độ và nhiều góc nhìn; có thể thử world landmarks/đa camera rồi đối chiếu dữ liệu chuẩn. Mỗi phần mở rộng phải có ground truth riêng.

## 12. Tài liệu

Nguồn và repo xem `RESEARCH.md`. Tài liệu OpenPose của đề dùng để giải thích hướng tiếp cận pose nói chung; chương trình sử dụng MediaPipe PoseLandmarker, không sử dụng OpenPose.
