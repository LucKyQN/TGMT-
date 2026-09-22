# Nguồn tham khảo và dữ liệu

Kiểm tra nguồn trực tuyến ngày 22/09/2026. Chỉ tham khảo kiến trúc/ý tưởng; không sao chép nguyên repo. Các tuyên bố trong README của tác giả chưa thay thế việc tái lập thực nghiệm trên máy của nhóm.

## Repo GitHub cùng ý tưởng

| Repo | Phần liên quan | Cách sử dụng trong đồ án |
|---|---|---|
| [m-soldo/mediapipe_exercise](https://github.com/m-soldo/mediapipe_exercise) | Góc khớp và đếm squat/push-up/pull-up | Đối chiếu máy trạng thái và cách chọn khớp; không lấy làm baseline của đề |
| [RiccardoRiccio/Fitness-AI-Trainer-With-Automatic-Exercise-Recognition-and-Counting](https://github.com/RiccardoRiccio/Fitness-AI-Trainer-With-Automatic-Exercise-Recognition-and-Counting) | Nhận diện bài tập và đếm; liên kết bộ dữ liệu đã chọn | Tham khảo phần dữ liệu/đánh giá; đồ án hiện chọn bài thủ công, không triển khai BiLSTM |
| [MichistaLin/mediapipe-Fitness-counter](https://github.com/MichistaLin/mediapipe-Fitness-counter) | MediaPipe + KNN, squat/push-up và video mẫu | So sánh cách phân loại tư thế với luật góc; không dùng số liệu của repo làm số liệu nhóm |

Bài liên quan của tác giả dataset: [Riccio, Real-Time Fitness Exercise Classification and Counting from Video Frames](https://arxiv.org/abs/2411.11548). Phải phân biệt accuracy nhận diện **loại bài** với accuracy **chấm kỹ thuật**; hai bài toán có nhãn khác nhau.

## Dataset đã xác minh

### Real-Time Exercise Recognition Dataset

- [Kaggle](https://www.kaggle.com/datasets/riccardoriccio/real-time-exercise-recognition-dataset), [bản do cùng tác giả đưa lên Hugging Face](https://huggingface.co/datasets/RickyRiccio/Real_Time_Exercise_Recognition_Dataset/tree/main).
- [Dataset card](https://huggingface.co/datasets/RickyRiccio/Real_Time_Exercise_Recognition_Dataset/blob/main/README.md) liệt kê squat, push-up, barbell bicep curl, shoulder press; không liệt kê plank.
- Có video người thật và avatar InfiniteRep, nhiều nguồn/góc quay. Bản HF hiển thị ZIP khoảng 3.09 GB tại thời điểm kiểm tra.
- Phù hợp để bổ sung squat/push-up và khảo sát tổng quát hóa. **Chưa xác minh có nhãn form hay rep count ở từng file**; không được tự coi tất cả là đúng kỹ thuật.
- Tải bằng nút Download của Kaggle hoặc ZIP ở HF, giải nén ngoài thư mục code rồi chọn các clip bên hông đưa vào `data/videos/realtime_real/` và `realtime_synthetic/`. Gán nhãn lại theo quy ước nhóm.
- Dataset card ghi CC BY-NC-SA 4.0; lưu nguồn và kiểm tra điều kiện của từng video nếu phân phối lại.

### Yoga Poses Dataset — Niharika Pandit

- [Đúng bộ dữ liệu đã chọn](https://www.kaggle.com/datasets/niharika41298/yoga-poses-dataset), **khác Yoga-82**.
- Ảnh được chia train/test, năm lớp, có plank. Tác giả mô tả ảnh thu thập qua Bing, có thể có watermark/text và nhiễu.
- Nhãn plank chỉ là loại tư thế. Cần kiểm tra thủ công trước khi dùng làm ví dụ form đúng.
- Ảnh tĩnh không đánh giá được rep, thời gian giữ hoặc độ ổn định theo thời gian. Dùng cho ví dụ hình học/kiểm tra pose, báo cáo tách khỏi video.
- Trang dữ liệu ghi quyền nội dung thuộc tác giả gốc; lưu nguồn ảnh nếu đưa vào slide.

## Phạm vi hiện đã thực hiện

Đã kiểm tra sự tồn tại và mô tả công khai; chưa tải toàn bộ hai dataset, chưa kiểm tra từng clip và chưa gán nhãn chúng. Không có dữ liệu thực nghiệm được tạo giả. Nguồn chính vẫn là video tự quay có nhãn thủ công của nhóm.

## Tài liệu nền tảng

- [MediaPipe Tasks Python](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/python): API, chế độ chạy và timestamp.
- [MediaPipe Pose Landmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker): 33 landmarks và model lite/full/heavy.
- [Cao et al., CVPR 2017](https://openaccess.thecvf.com/content_cvpr_2017/html/Cao_Realtime_Multi-Person_2D_CVPR_2017_paper.html): OpenPose/Part Affinity Fields là tài liệu nền, không phải model đang chạy trong ứng dụng.
