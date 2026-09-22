# Demo và bảo vệ

## Kịch bản khoảng 5 phút

1. **0:00–0:30:** nói bài toán, bật `run_demo.bat`; giải thích người dùng chọn bài, camera bên hông. Chỉ ra góc, stage, FPS và bộ đếm.
2. **0:30–1:30:** squat 2–3 lần rõ ràng. Dừng ở đáy cho thấy chưa đếm, đứng lên mới đếm. Làm một rep nông trong phạm vi thoải mái để hiện `SHALLOW`.
3. **1:30–2:30:** nhấn 2, chống tay lên rồi hít đất. Chỉ ra góc khuỷu và đường thân. Các ca lỗi khó minh họa live nên dùng video đã quay/gán nhãn.
4. **2:30–3:15:** nhấn 3. Đứng thẳng cho thấy đồng hồ không chạy, vào plank để đồng hồ chạy, dừng tư thế để thấy dừng cộng.
5. **3:15–3:45:** ra khỏi khung hình: hiện mất dấu, không tự thêm rep. Vào lại phải xác nhận tư thế bắt đầu.
6. **3:45–4:30:** Q; mở thư mục session, chỉ ra raw/demo, dòng rep và lỗi tương ứng.
7. **4:30–5:00:** mở bảng `comparison.md` của tập test đã gán nhãn; nêu một ca sai và giới hạn. Nếu chưa có số liệu thì nói chưa đo, không trình bày số minh họa thành kết quả.

Chuẩn bị video dự phòng trên máy. Trước buổi báo cáo kiểm tra quyền camera, pin/nguồn điện, màn hình chiếu và đường dẫn model offline. Không cần Internet khi chạy ứng dụng đã tải model.

## Kế hoạch 30 clip tự quay

| Bài | 10 clip dự kiến | Nhãn cần có |
|---|---|---|
| Squat | 4 clip đạt; 2 nông; 2 thay đổi nghiêng thân; 1 đổi tốc độ; 1 che khuất | Tổng rep, end_s, form từng rep |
| Hít đất | 4 đạt; 2 nông; 2 sai đường thân; 1 đổi tốc độ; 1 che khuất | Tổng rep, end_s, form từng rep |
| Plank | 4 giữ ổn định; 2 hông nhô; 2 lệch đường thân; 1 đứng trước khi vào bài; 1 mất dấu | Khoảng bắt đầu/kết thúc form đúng; tổng giây |

Đây là kế hoạch, chưa phải dữ liệu đã thu. Ghi rõ `subject`, buổi quay, nguồn và split. Lỗi có chủ ý chỉ minh họa trong phạm vi vận động thoải mái; có thể dùng video sẵn phù hợp thay cho cố làm lỗi. Không cần dùng tạ.

Gán nhãn từ video gốc không có dự đoán hiển thị để giảm thiên lệch. Xem chậm khi cần, ghi timestamp theo file. Sau khi chốt nhãn mới xem demo có HUD để phân tích sai khác.

## Câu hỏi giảng viên dễ hỏi

**Nhóm có tự huấn luyện AI không?**  
Không. MediaPipe là pose model có sẵn; đóng góp là hình học pixel, trạng thái có kiểm soát nhiễu, ba bài, log và quy trình đánh giá.

**Tại sao dùng pixel?**  
`x` và `y` normalized theo W và H khác nhau. Tích vô hướng trên các trục đã co giãn khác nhau làm sai góc. Nhân W,H khôi phục tỉ lệ ảnh.

**Tại sao đếm khi lên?**  
Đếm chu kỳ hoàn thành; xuống rồi bỏ dở chưa phải một lần lên–xuống hoàn chỉnh theo quy ước này.

**Squat chưa xuống 100° có được đếm không?**  
Có nếu qua ngưỡng bắt đầu 145° rồi trở lại 160° đủ lâu, nhưng nhãn `SHALLOW`. Nhờ đó nhánh sai thực sự có thể xảy ra.

**Ngưỡng từ đâu ra?**  
160/100 xuất phát starter, các ngưỡng khác là giả thuyết kỹ thuật. Chúng cần tune trên dev; không nói đây là chuẩn y khoa hoặc phù hợp mọi người.

**Có phát hiện lưng cong không?**  
Chưa. Vai–hông–mắt cá và độ nghiêng thân không đo hình dạng cột sống. Chỉ gọi đúng tên đại lượng đang đo.

**Đứng thẳng cũng có góc thân 180° thì sao?**  
Plank còn cần thân gần nằm ngang. Tuy vậy nằm nghỉ thẳng người vẫn có thể qua luật; hiện giả định người dùng thực hiện bài đã chọn.

**FPS thấp có làm plank ít giây hơn không?**  
File dùng frame_idx/FPS, không dùng thời gian xử lý. Webcam dùng đồng hồ đơn điệu. Mất dấu/khoảng gap dài sẽ ngừng cộng theo quy tắc.

**Tại sao Lite không chắc kém Full?**  
Tên model không chứng minh accuracy trên tập của nhóm. So sánh cùng video và nhãn, cùng phần cứng; ghi FPS và sai số riêng.

**Một video có đúng và sai thì F1 tính ra sao?**  
Đánh nhãn mixed, dùng nhãn từng rep và ghép theo thời điểm. Không gán một nhãn duy nhất cho mọi rep trong clip.

**Tại sao confusion matrix có ba cột?**  
Có `unknown` khi thiếu thông tin. Không ép thiếu quan sát thành kỹ thuật sai; vẫn đưa các ca này vào độ phủ và recall để không làm đẹp kết quả.

**Ảnh plank trong Yoga có phải ground truth kỹ thuật đúng?**  
Không tự động. Nhãn thể loại không phải nhãn chất lượng. Phải xem lại; ảnh không đo được thời gian.

**Giảm sai số đến đâu?**  
Chỉ trả lời bằng bảng đã chạy trên tập test. Kiểm thử logic qua không chứng minh accuracy trên người thật.
