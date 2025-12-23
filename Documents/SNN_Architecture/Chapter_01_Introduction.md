# Chương 01: Đặt vấn đề & Tầm nhìn (Context & Vision)

---

## 1.1 Khơi nguồn Vấn đề

Dự án EmotionAgent đối mặt với một thách thức cốt lõi: **Làm thế nào để tạo ra một Agent AI có khả năng "Cảm xúc" và "Thích nghi" trong môi trường luôn biến động, mà không rơi vào các lối mòn của Deep Learning truyền thống?**

Các mô hình Deep Learning (MLP/Transformer) hiện nay, dù rất mạnh mẽ, nhưng gặp phải những rào cản chí mạng khi áp dụng cho bài toán này:

1.  **Sự Vô nghĩa của Vector (Semantic Opacity):**
    *   MLP ép buộc mọi trạng thái cảm xúc vào các vector số học dày đặc (Dense Vectors), ví dụ `[0.1, 0.9, -0.5]`.
    *   *Hệ quả:* Chúng ta không thể giải thích tại sao Agent lại "Vui" hay "Buồn". Mọi thứ là một hộp đen toán học vô hồn.
2.  **Chi phí Tính toán Bất hợp lý (Computational Waste):**
    *   Để xử lý một thay đổi nhỏ, toàn bộ ma trận trọng số khổng lồ phải được tính toán lại ($O(N^2)$).
    *   *Hệ quả:* Lãng phí năng lượng, khó chạy realtime trên thiết bị giới hạn.
3.  **Học tập Thụ động & Quên (Catastrophic Forgetting):**
    *   MLP cần dữ liệu lớn và học offline. Khi học cái mới, nó có xu hướng ghi đè lên cái cũ.
    *   *Hệ quả:* Agent không thể thích nghi tức thì (Online Learning) với môi trường thay đổi liên tục.

## 1.2 Tầm nhìn: "Kỹ thuật Phi Nhân" (Un-human Engineering)

Chúng ta đề xuất một hướng tiếp cận hoàn toàn mới, gọi là **"Computational SNN"**.

Thay vì cố gắng mô phỏng sinh học não bộ một cách mù quáng (Bio-mimicry) hay chạy đua về điểm số Benchmark, chúng ta tiếp cận SNN dưới góc độ **Kỹ thuật Phần mềm (Software Engineering)**:

*   **Không phải Sinh học:** Chúng ta không quan tâm tế bào thần kinh trông như thế nào. Chúng ta quan tâm nó *xử lý thông tin* như thế nào.
*   **Hiệu năng là cốt lõi:** Một "Neuron Số" (Digital Neuron) chính xác tuyệt đối có sức mạnh bằng hàng ngàn neuron sinh học ồn ào.
*   **Minh bạch:** Cấu trúc mạng phải có thể đọc hiểu được như một Cơ sở dữ liệu (Database).

## 1.3 Mục tiêu Cụ thể

1.  **Tiết kiệm:** Loại bỏ phép nhân ma trận. Chỉ sử dụng phép cộng và so sánh.
2.  **Thích nghi:** Agent phải học được quy luật nhân quả ngay sau 1 lần trải nghiệm (One-shot Learning).
3.  **Bền vững:** Học cái mới không được quên cái cũ (Stability-Plasticity Dilemma).
4.  **Hòa nhập:** SNN không thay thế Logic (RL), mà đóng vai trò là "Nhạc trưởng Cảm xúc" điều phối Logic.
