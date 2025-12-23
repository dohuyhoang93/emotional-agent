# SNN Failure Prevention Strategy

Để mô hình SNN tự thiết kế này không bị thất bại (về mặt kỹ thuật hoặc chức năng), chúng ta cần kiểm soát chặt chẽ 4 khía cạnh rủi ro sau đây. Đây là những "bẫy" mà hầu hết các dự án SNN custom đều mắc phải.

---

## 1. Rủi ro về "Cái chết im lặng" (The Dead Network)

*   **Vấn đề:** Sau một thời gian hoạt động, mạng nơ-ron có thể rơi vào hai trạng thái cực đoan:
    1.  **Im lặng tuyệt đối (Silence):** Ngưỡng kích hoạt quá cao hoặc trọng số quá thấp -> Không ai bắn xung -> Không học được gì.
    2.  **Động kinh (Epilepsy):** Ngưỡng quá thấp -> Mọi neuron đều bắn liên tục -> Nhiễu loạn thông tin -> Tràn bộ đệm sự kiện.
*   **Giải pháp (Cần cài đặt):** **Cơ chế Cân bằng nội môi (Homeostasis).**
    *   Mỗi neuron phải có một "target firing rate" (tần số bắn mục tiêu).
    *   Nếu bắn quá nhiều -> Tự động tăng ngưỡng kích hoạt (khó tính hơn).
    *   Nếu bắn quá ít -> Tự động giảm ngưỡng (dễ tính hơn).
    *   *Điều này đảm bảo mạng luôn "sống" và duy trì hoạt động ở mức năng lượng tối ưu.*

## 2. Rủi ro về "Học điều vô nghĩa" (Learning Noise)

*   **Vấn đề:** Quy tắc STDP rất nhạy cảm. Nếu môi trường có nhiễu (ngẫu nhiên), STDP vẫn sẽ cố gắng tìm ra quy luật (dù không có quy luật nào). Kết quả là Agent hình thành các "mê tín dị đoan" (Superstitions) - tin vào những mối liên hệ nhân quả không có thật.
*   **Giải pháp:** **Cổng Dopamine (Three-factor Rule).**
    *   Không cho phép STDP tự do cập nhật trọng số mọi lúc.
    *   Chỉ cho phép cập nhật mạnh khi có tín hiệu **Reward (hoặc Punishment)** từ môi trường xác nhận hành động đó là đúng.
    *   *Nguyên tắc: "Chỉ tin vào nhân quả khi nó mang lại kết quả thực tế."*

## 3. Rủi ro về "Bùng nổ Hiệu năng" (Performance Explosion)

*   **Vấn đề:** Chúng ta dùng Database/ECS để ảo hóa 1 triệu neuron. Tuy nhiên, nếu thiết kế truy vấn (Query) không tốt, việc quét qua database mỗi milisecond sẽ làm treo máy (CPU 100%).
*   **Giải pháp:** **Kiến trúc Sự kiện triệt để (Strict Event-Driven).**
    *   Tuyệt đối không dùng vòng lặp `for all_neurons`.
    *   Chỉ dùng `Select * from Synapses where SourceID in (List_Spiked_Neurons)`.
    *   Tận dụng Indexing của Database tối đa.
    *   *Kỷ luật kỹ thuật: Nếu một Query tốn quá 5ms, phải thiết kế lại Schema.*

## 4. Rủi ro về "Sự cô lập Logic" (Logic Isolation)

*   **Vấn đề:** Chúng ta tách SNN (Cảm xúc) và RL (Logic). Rủi ro là hai hệ thống này không "hiểu" nhau. Tín hiệu từ SNN gửi sang (ví dụ: Fear=0.9) nhưng RL không biết làm gì với con số đó (hoặc trọng số của RL cho tín hiệu này quá thấp).
*   **Giải pháp:** **Cơ chế Mapping rõ ràng & Meta-Learning.**
    *   Phải định nghĩa cứng (ban đầu) các tác động: `Fear -> Giảm Exploration Rate`.
    *   Sau đó cho phép Meta-Learning điều chỉnh cường độ này.
    *   *Đừng để hệ thống tự đoán ý nghĩa của Cảm xúc ngay từ đầu. Hãy Hard-code các bản năng sinh tồn cơ bản (Intrinsic Motivations) trước.*

---

### Tổng kết Checklist cho giai đoạn Code:

1.  [ ] Cài đặt **Adaptive Threshold** (Homeostasis) ngay trong `Neuron Struct`.
2.  [ ] Cài đặt **Reward-Modulated STDP** thay vì STDP thuần.
3.  [ ] Benchmark hiệu năng Query (Read/Write) với 10,000 neuron giả lập trước khi làm logic.
4.  [ ] Định nghĩa Interface giao tiếp SNN->RL rõ ràng (đừng để nó là hộp đen).
