# Các Đề xuất Cải tiến SNN (Giải thích Chi tiết)

Tài liệu này giải thích 3 cơ chế bổ sung cần thiết để SNN hoạt động ổn định và thông minh hơn, dựa trên phân tích các điểm còn thiếu của thiết kế hiện tại.

---

## 1. Độ trễ Thời gian (Temporal Delays)

### Khái niệm
Trong dây thần kinh thật, tín hiệu không đi tức thì. Nó mất thời gian để truyền từ A đến B. Khoảng thời gian này gọi là **Delay**.

### Tại sao cần?
Nếu không có Delay, toàn bộ mạng sẽ hoạt động như một hàm số tức thời (`y = f(x)`). Mạng sẽ mất khả năng cảm nhận **Trình tự (Sequence)** và **Nhịp điệu (Rhythm)**.
*   *Ví dụ:* Để phân biệt "Con Cọp gầm" (nguy hiểm) và "Con Mèo kêu" (an toàn), mạng cần biết độ dài và khoảng cách giữa các âm thanh. Delay chính là bộ nhớ ngắn hạn tự nhiên.

### Cài đặt thế nào? (Trong Database)
Thêm trường `delay` vào bảng Synapse.
*   **Database:** `{SourceID, TargetID, Weight, Delay_ms}`
*   **Logic:** Khi Neuron A bắn xung tại thời điểm `t`, xung này sẽ được đưa vào "Hàng đợi Sự kiện" để đánh thức Neuron B tại thời điểm `t + Delay_ms`, chứ không phải đánh thức ngay lập tức.

---

## 2. Ức chế Bên & "Người thắng lấy tất" (Lateral Inhibition & Winner-Take-All)

### Khái niệm
Các neuron thường được tổ chức thành các lớp (Layer). Trong cùng một lớp, các neuron là đối thủ của nhau.
**Luật:** "Nếu tao nói, mày phải im mồm."

### Tại sao cần?
Nếu không có ức chế, khi có tín hiệu vào, tất cả neuron hơi liên quan đều bắn xung loạn xạ. Tín hiệu bị "nhòe" (Blur).
Ức chế bên giúp **làm nét (Sharpen)** tín hiệu: Chỉ có neuron phản ứng mạnh nhất mới được quyền bắn xung, các neuron yếu hơn bị dập tắt. Điều này ép các neuron phải **Chuyên môn hóa** (Mỗi thằng chỉ giỏi một việc).

### Cài đặt thế nào?
Sử dụng một Process đặc biệt tên là `process_lateral_inhibition`.
*   **Logic:** Khi một nhóm neuron cùng nhận tín hiệu, process này sẽ tìm ra neuron có điện thế cao nhất (`max_potential`).
*   Nó sẽ gửi tín hiệu ức chế (tín hiệu âm) đến tất cả các neuron hàng xóm, triệt tiêu điện thế của chúng về 0.

---

## 3. Thuyết Tiến hóa Thần kinh (Neural Darwinism)

### Khái niệm
Đừng nuôi báo cô các neuron vô dụng. Mạng lưới là một đấu trường sinh tồn.

### Tại sao cần?
Chúng ta muốn mạng tự lớn lên (Neurogenesis). Nhưng nếu chỉ sinh ra mà không chết đi, mạng sẽ phình to vô hạn và làm sập RAM/Database.
Chúng ta cần một cơ chế dọn rác thông minh: **Apoptosis (Chết tế bào theo chương trình)**.

### Cài đặt thế nào?
Thêm chỉ số `utility_score` (điểm hữu dụng) cho mỗi neuron/synapse.
*   **Tăng điểm:** Mỗi khi neuron tham gia vào một dự đoán đúng (có Reward).
*   **Giảm điểm:** Mỗi chu kỳ thời gian (Rò rỉ/Lão hóa).
*   **Thanh trừng:** Định kỳ (ví dụ mỗi 1000 bước), chạy một Process quét DB: `DELETE FROM Neurons WHERE utility_score < Threshold`.
*   *Kết quả:* Mạng sẽ tự động co lại những vùng không dùng đến và phình to ở những vùng đang học cái mới. Tối ưu hóa tài nguyên tự động.

---
**Tóm lại:**
1.  **Delay:** Để hiểu thời gian/trình tự.
2.  **Inhibition:** Để làm nét tín hiệu và ép chuyên môn hóa.
3.  **Darwinism:** Để quản lý tài nguyên và loại bỏ rác.
