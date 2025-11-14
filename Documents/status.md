# Trạng thái Dự án: EmotionAgent

---
*Tài liệu này được cập nhật theo thời gian để ghi lại tiến trình, các kết quả thử nghiệm và những thay đổi trong định hướng của dự án. Các cập nhật mới nhất sẽ được thêm vào cuối tệp.*
---

## Giai đoạn 1: Prototype Tác nhân Đơn lẻ (Ngày 13/11/2025)

### 1.1. Mục tiêu
Hoàn thành việc triển khai **Bước 1: Prototype tác nhân đơn lẻ** theo tầm nhìn đã được thống nhất trong `spec.md` và triết lý Kiến trúc Hướng Quy trình (POP).

### 1.2. Tổng kết
Tính khả thi của mô hình cốt lõi đã được chứng minh ở cấp độ prototype. Đã xây dựng một tác nhân có khả năng học hỏi thông qua Q-Learning, với một vòng lặp phản hồi Trí tuệ-Cảm xúc tích hợp.

### 1.3. Trạng thái các thành phần khi hoàn thành Giai đoạn 1

#### A. Các thành phần đã hoàn thiện:
*   **Kiến trúc Hướng Quy trình (POP):** Đã triển khai đầy đủ và hoạt động ổn định (Workflow Engine, Process Registry, AgentContext, cấu trúc thư mục).
*   **Môi trường (`GridWorld`):** Hoàn chỉnh cho mục đích thử nghiệm Giai đoạn 1.
*   **Cơ chế học hỏi cốt lõi (Q-Learning):** Đã triển khai đầy đủ, bao gồm cập nhật Q-table và chiến lược chọn hành động epsilon-greedy.
*   **Mô hình Cảm xúc Máy (MLP):** Đã được định nghĩa, tích hợp và huấn luyện với mục tiêu kép (tự tin và tò mò).
*   **Vòng lặp phản hồi Trí tuệ-Cảm xúc:** Đã được kết nối hoàn chỉnh và hoạt động.
*   **Các Process:** `p1` đến `p8` đã hoàn thiện các chức năng cơ bản.

#### B. Các thành phần vẫn là Placeholder hoặc cần mở rộng/tinh chỉnh:
1.  **Bộ nhớ dài hạn (`long_term_memory`):** Hoàn toàn chưa được triển khai.
2.  **Sử dụng Bộ nhớ ngắn hạn (`short_term_memory`):** Mới chỉ được sử dụng ở mức cơ bản.
3.  **`p2_belief_update.py` (Cập nhật Niềm tin):** Logic còn cơ bản, có thể mở rộng.
4.  **`N_vector` (Vector Nhu cầu):** Hiện tại là tĩnh.
5.  **Các chiều khác của `E_vector`:** Hiện tại chỉ huấn luyện 2 chiều.

---

## Giai đoạn 2: Xây dựng Hệ thống Dàn dựng Thử nghiệm (Ngày 14/11/2025)

### 2.1. Mục tiêu
Xây dựng một hệ thống tự động để chạy các thử nghiệm quy mô lớn, thu thập dữ liệu và phân tích một cách khoa học, tuân thủ triết lý POP.

### 2.2. Tổng kết
Hệ thống đã hoàn thiện, cho phép cấu hình và thực thi các kịch bản thử nghiệm phức tạp một cách tự động.

### 2.3. Trạng thái các thành phần khi hoàn thành Giai đoạn 2
*   **Kiến trúc POP:** Toàn bộ hệ thống dàn dựng được thiết kế tuân thủ triết lý POP.
*   **Các thành phần chính:**
    *   **`experiments.json`:** Tệp cấu hình trung tâm.
    *   **`run_experiments.py`:** Bộ máy thực thi (Workflow Engine) chính.
    *   **`main.py` (Worker):** Được tái cấu trúc để hoạt động như một "worker" độc lập.
    *   **`src/orchestration_processes/`:** Thư mục chứa các quy trình độc lập cho từng bước dàn dựng.
*   **Tính năng:** Hệ thống có khả năng chạy N thử nghiệm, mỗi thử nghiệm M lần, tự động thu thập kết quả, vẽ biểu đồ tổng hợp và tạo báo cáo phân tích.

---

## Nhật ký Chạy thử và Phân tích

### Chạy thử lần 1 (Ngày 13/11/2025) - Môi trường Đơn giản
*   **Mục tiêu:** Thử nghiệm ban đầu sau khi hoàn thiện Giai đoạn 1.
*   **Thiết lập:** 500 episodes, môi trường 5x5.
*   **Kết quả:** Tỷ lệ thành công: 15.6%.
*   **Đánh giá:** Hiệu suất giảm đáng kể so với các phiên bản sơ khai. **Câu hỏi đặt ra: Tại sao?** Nguyên nhân tiềm năng được cho là do xung đột cơ chế hoặc siêu tham số chưa phù hợp.

### Chạy thử lần 2 (Ngày 14/11/2025): So sánh Mức độ Tò mò trong Môi trường Đơn giản
*   **Mục tiêu:** Tìm hiểu nguyên nhân của sự suy giảm hiệu suất bằng cách so sánh ảnh hưởng của `intrinsic_reward_weight`.
*   **Thiết lập:** Môi trường 5x5, 3 thử nghiệm (Low/Baseline/High Curiosity), mỗi thử nghiệm chạy 3 lần, 1000 episode/lần.
*   **Kết quả:** Agent `Low_Curiosity` (ít tò mò) cho hiệu suất tốt nhất (Tỷ lệ thành công 35.00%).
*   **Phân tích:**
    *   **Giả thuyết về sự "Xao lãng" (The "Distraction" Hypothesis):** Trong môi trường đơn giản, phần thưởng nội sinh (sự tò mò) hoạt động như một yếu tố gây xao lãng, khuyến khích agent khám phá những hành vi vô ích thay vì tập trung vào mục tiêu chính.
    *   **Kết luận:** Sự suy giảm hiệu suất không phải là lỗi, mà là một đặc tính của mô hình. Hiệu quả của sự tò mò phụ thuộc vào độ phức tạp của môi trường.

### Chạy thử lần 3 (Ngày 14/11/2025): Kiểm chứng Giả thuyết Tò mò trong Môi trường Phức tạp
*   **Mục tiêu:** Kiểm chứng giả thuyết rằng sự tò mò sẽ có lợi trong môi trường phức tạp hơn.
*   **Thiết lập Môi trường:** Lưới 15x15, có nhiều tường, số bước tối đa 250.
*   **Thiết lập Thử nghiệm:** 2 thử nghiệm (Complex_Low_Curiosity và Complex_High_Curiosity), mỗi thử nghiệm chạy 3 lần, 2000 episode/lần.
*   **Kết quả:** Agent `Complex_Low_Curiosity` vẫn cho hiệu suất tốt hơn (Tỷ lệ thành công 43.58% so với 35.62%).
*   **Phân tích:**
    *   **Giả thuyết KHÔNG được xác nhận:** Việc tăng độ phức tạp về không gian và chướng ngại vật là chưa đủ để làm cho sự tò mò trở nên có lợi.
    *   **Giả thuyết "Xao lãng" được củng cố:** Agent `High_Curiosity` vẫn bị "lạc lối" trong việc khám phá những điều mới lạ nhưng không giúp đạt được mục tiêu.
    *   **Lý do:** Môi trường tuy phức tạp hơn về không gian nhưng vẫn có thể đoán trước được (deterministic). Các "bất ngờ" vẫn chưa đủ "thú vị" và mang tính toàn cục.
*   **Hướng đi tiếp theo:**
    Để thực sự kiểm chứng giá trị của sự tò mò, cần một môi trường mà ở đó, việc chỉ khám phá ngẫu nhiên là gần như vô vọng. **Bước tiếp theo hợp lý nhất là giới thiệu yếu tố Ngẫu nhiên (Stochasticity) vào Môi trường.**
    *   **Ý tưởng:** Thay đổi môi trường để các hành động của agent không còn đáng tin cậy 100% (ví dụ: bị "trượt").
    *   **Kỳ vọng:** Trong một thế giới không thể đoán trước, khả năng mô hình hóa và hiểu các kết quả "bất ngờ" của agent `High_Curiosity` có thể sẽ trở nên có giá trị hơn.

---
---

## Mẫu Cập nhật Trạng thái Thử nghiệm (Template)

*Sao chép và điền thông tin cho các lần chạy thử nghiệm trong tương lai.*

### Chạy thử lần X (Ngày XX/XX/XXXX): [Tên thử nghiệm]
*   **Mục tiêu:** [Mô tả mục tiêu của thử nghiệm này]
*   **Thiết lập Môi trường:** [Mô tả các thay đổi về môi trường, ví dụ: Stochastic, Slippery=0.2]
*   **Thiết lập Thử nghiệm:** [Mô tả các nhóm thử nghiệm, số lần chạy, số episode]
*   **Kết quả:** [Bảng hoặc tóm tắt kết quả chính]
*   **Phân tích:** [Phân tích kết quả, giả thuyết có được xác nhận không, tại sao?]
*   **Hướng đi tiếp theo:** [Dựa trên kết quả, bước tiếp theo là gì?]
