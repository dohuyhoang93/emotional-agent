# Chương 02: Cơ sở Lý thuyết (Theoretical Core) - Consolidated

Chương này tổng hợp toàn bộ nền tảng lý thuyết của kiến trúc SNN, từ cơ học neuron cơ bản đến các cơ chế xã hội, cam kết tri thức và khả năng tưởng tượng.

---

## 2.1 Hebbian Learning Hiện đại & R-STDP

Cơ chế cốt lõi của hệ thống là **Học Hebbian Điều biến bởi Phần thưởng (Reward-modulated Hebbian Learning)**.

### 2.1.1 Quy tắc 3 Yếu tố (Three-Factor Rules)
Không chỉ là "Neurons that fire together, wire together". Chúng ta cần yếu tố thứ 3 là **Dopamine ($D$)** để hướng dẫn việc học.
*   Công thức: $\Delta w = \eta \cdot \text{Eligibility Trace} \cdot D(t)$

### 2.1.2 Giải quyết Gán tín dụng tầm xa (Synaptic Tagging)
Để giải quyết việc phần thưởng đến chậm (Credit Assignment Problem):
*   Sử dụng **Đa Trace (Multi-timescale Traces)**:
    *   **Fast Trace ($z_{fast}$):** Phân rã nhanh (ms) cho quan hệ nhân quả tức thì.
    *   **Slow Trace ($z_{slow}$):** Phân rã chậm (phút) đóng vai trò "Synaptic Tag".
*   Khi Dopamine đến muộn, nó kích hoạt các $z_{slow}$ còn sót lại để cập nhật trọng số.

---

## 2.2 Logic Chủ động & Đối thoại 2 Chiều (Bidirectional Dialogue)

Mối quan hệ SNN - RL là một cuộc đối thoại thay vì luồng một chiều.

### 2.2.1 SNN -> RL: Population Code (Mã hóa Quần thể)
Thay vì xuất ra một con số vô hướng `Fear = 0.8` (mất thông tin), SNN xuất ra một **Semantic Vector** mật độ cao.
*   Vector này mã hóa chi tiết: Sợ cái gì? Ở đâu? Cường độ ra sao?
*   Giúp RL Agent có đủ ngữ cảnh để ra quyết định phức tạp.

### 2.2.2 RL -> SNN: Top-down Modulation (Điều biến từ trên xuống)
RL Agent không thụ động. Nó chủ động điều khiển SNN:
*   **Attention:** Tăng độ nhạy (giảm ngưỡng) vùng vỏ não thính giác khi cần nghe ngóng.
*   **Suppression:** Ức chế vùng sợ hãi khi cần thực hiện hành động mạo hiểm.

---

## 2.3 Lý thuyết Tín hiệu Vector (Vector Signal Theory)

Chúng ta định nghĩa lại đơn vị thông tin cơ bản: **Spike là một Vector**, không phải bit nhị phân.

### 2.3.1 Vector Spike
Xung thần kinh $\vec{S} \in \mathbb{R}^{16}$. Mỗi chiều đại diện cho một đặc tính (Màu sắc, Hướng, Tần số).

### 2.3.2 Neuron là Bộ lọc Vector (Vector Filter)
Neuron thực hiện phép **So khớp Mẫu (Pattern Matching)**.
*   Mỗi Neuron có một **Vector Mẫu (Prototype Vector)**.
*   Điều kiện kích hoạt: Kích hoạt khi Input có **Độ tương đồng Cosine (Cosine Similarity)** cao với Vector Mẫu.
*   **Học Không gian:** Neuron tự động xoay Vector Mẫu về phía các cụm tín hiệu thường gặp (Unsupervised Clustering).

---

## 2.4 Cân bằng Nội môi (Homeostasis & Meta-Homeostasis)

Để chặn đứng rủi ro "Động kinh" hoặc "Chết não".

*   **Adaptive Threshold:** Tự động tăng ngưỡng khi bắn quá nhiều, giảm khi bắn quá ít.
*   **PID Control:** Duy trì Global Firing Rate ở mức mục tiêu 1-2%.

---

## 2.5 Mảnh ghép Quyết định: Lớp Cam kết (The Commitment Layer)

Tầng logic cao nhất, đóng vai trò "Tòa án Tri thức".

### 2.5.1 Chuyển pha Tri thức
Tri thức trải qua 3 trạng thái vật lý:
1.  **Lỏng (Fluid):** Đang học, dễ thay đổi (High Plasticity).
2.  **Rắn (Solid):** Đã cam kết. Khóa cứng (`frozen=True`). Dùng cho trí nhớ dài hạn.
3.  **Bác bỏ (Revoked):** Khi kiến thức rắn sai liên tục -> Phá vỡ cam kết, quay lại trạng thái lỏng.

### 2.5.2 Vai trò Bảo chứng
Lớp Cam kết ngăn chặn việc "học đè" (Catastrophic Forgetting) và cung cấp sự ổn định cần thiết cho hệ thống ra quyết định.

---

## 2.6 Cơ chế Tưởng tượng (Imagination & Internal Simulation)

Một bước nhảy vọt quan trọng: SNN không chỉ phản ứng với hiện tại, nó có thể **tách rời giác quan** để mô phỏng tương lai.

### 2.6.1 Không gian Tưởng tượng (Imaginary Space)
*   SNN có 2 chế độ hoạt động:
    1.  **Online (Thức):** Input đến từ Sensor. Output điều khiển Motor.
    2.  **Offline (Mơ/Tưởng tượng):** Input bị ngắt (Sleep paralysis). Input được thay thế bởi **Tín hiệu Tự sinh (Self-generated Spikes)**.

### 2.6.2 Học Nhân quả trong Tưởng tượng
*   Trong chế độ Mơ, SNN tái hiện lại các ký ức cũ hoặc xáo trộn chúng ngẫu nhiên (Replay & Remix).
*   Nếu chuỗi tưởng tượng dẫn đến trạng thái "Đau đớn" (Pain Prediction):
    *   Hệ thống ghi nhớ chuỗi nhân quả này.
    *   Tạo ra một **"Chính sách Phản xạ" (Reflex Policy)**: "Nếu thấy dấu hiệu đầu tiên của chuỗi này -> Ức chế ngay lập tức."
*   *Kết quả:* Agent học được cách tránh rủi ro mà không cần phải thực sự trải qua nó trong thực tế.
