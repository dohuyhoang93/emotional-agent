# Chương 08: Kế hoạch Triển khai & Kết luận (Roadmap)

---

## 8.1 Lộ trình Thực hiện (Implementation Roadmap)

Chúng ta chia việc triển khai thành 3 giai đoạn chính (Phases) để giảm rủi ro.

### Giai đoạn 1: Bộ khung SNN (The SNN Skeleton)
*   **Mục tiêu:** Xây dựng cấu trúc dữ liệu và vòng lặp sự kiện cơ bản. Chưa có học (Learning).
*   **Công việc:**
    1.  [ ] Định nghĩa `SnnContext` trong `src/core/context.py`.
    2.  [ ] Xây dựng Database Schema (In-memory dict hoặc SQLite/Redb) cho Neuron/Synapse.
    3.  [ ] Viết `process_integrate` và `process_propagate` (có xử lý Delay).
    4.  [ ] **Unit Test:** Kiểm tra một xung đơn chạy qua chuỗi neuron A -> B -> C đúng thời gian.

### Giai đoạn 2: Sự sống & Thích nghi (Life & Adaptation)
*   **Mục tiêu:** Mạng tự điều chỉnh để không chết.
*   **Công việc:**
    1.  [ ] Cài đặt `process_homeostasis` (Adaptive Threshold).
    2.  [ ] Cài đặt `process_lateral_inhibition` (WTA).
    3.  [ ] Chạy thử nghiệm với Random Input: Mạng phải duy trì hoạt động ổn định (không im lặng, không động kinh).

### Giai đoạn 3: Trí tuệ & Học (Intelligence & Learning)
*   **Mục tiêu:** Mạng học được quy luật nhân quả.
*   **Công việc:**
    1.  [ ] Cài đặt `process_stdp_learning` (3-factor rule).
    2.  [ ] Tích hợp Reward từ môi trường vào SNN.
    3.  [ ] Kết nối Output của SNN vào tham số RL (Exploration Rate).
    4.  [ ] **Thử nghiệm:** Cho Agent chạy trong môi trường Maze. Kiểm tra xem nó có học sợ "Cửa Đỏ" (nơi có bẫy) sau vài lần đau không.

---

## 8.2 Kết luận

Dự án EmotionAgent đang tiên phong trong việc áp dụng SNN theo hướng **Kỹ thuật Phần mềm (Software Engineering)**.
Chúng ta không đi theo lối mòn của Deep Learning (chính xác nhưng cứng nhắc), mà chọn con đường **Thích nghi & Bền bỉ**.

Bằng cách kết hợp:
*   **Cấu trúc dữ liệu Database/ECS** (Hiệu năng, Quy mô).
*   **Logic SNN Hebbian** (Học nhân quả, Online).
*   **Kiến trúc Theus POP** (Minh bạch, Modun hóa).

Chúng ta kỳ vọng tạo ra một thế hệ Agent có khả năng "Cảm nhận" thực sự thông qua cơ chế vật lý của sự tương tác, chứ không phải qua các bảng số vô hồn.

**Bước tiếp theo:** Bắt đầu Code Giai đoạn 1.
