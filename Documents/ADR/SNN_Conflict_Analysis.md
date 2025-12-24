# Phân tích Xung đột Kiến trúc & Giải pháp (Architectural Conflict Analysis)

Tài liệu này đi sâu vào phân tích 3 điểm nghẽn logic (Logical Deadlocks) có thể khiến hệ thống thất bại, và đề xuất cơ chế giải quyết cụ thể.

---

## 1. Xung đột: Cam kết (Internal Stability) vs. Xã hội (External Influence)

### 1.1 Bản chất Xung đột
*   **Cơ chế Commitment:** Khi một tri thức (Synapse) đạt trạng thái `SOLID` (Rắn), nó bị khóa cứng (`frozen=True`) để bảo vệ khỏi nhiễu và quên lãng.
*   **Cơ chế Viral Learning:** Một "Gói Gen Synapse" từ Agent khác (có thể mâu thuẫn với tri thức rắn hiện tại) được nạp vào mạng.
*   **Vấn đề:** Nếu ta cho phép Gen ngoại lai ghi đè -> Phá vỡ tính ổn định (Commitment vô nghĩa). Nếu ta từ chối -> Phá vỡ tính thích nghi (Bảo thủ, không học được cái hay của người khác). Hơn nữa, làm sao biết cái mới tốt hơn cái cũ nếu không thử?

### 1.2 Giải pháp: Cơ chế "Sandbox Ký sinh" (Parasitic Sandbox)

Chúng ta coi Gen ngoại lai như một virus ký sinh, nhưng chạy trong môi trường bị cách ly (Sandbox).

*   **Bước 1: Tiếp nhận (Infection):**
    *   Không ghi đè Synapse cũ.
    *   Tạo ra một **Synapse Bóng ma (Shadow Synapse)** chạy song song với Synapse Rắn.
    *   Synapse Bóng ma ở trạng thái `FLUID` (Lỏng) và có trọng số ban đầu thấp.

*   **Bước 2: Cuộc đua Ngầm (The Shadow Race):**
    *   Khi Neuron kích hoạt, cả Synapse Rắn và Bóng ma đều đưa ra dự đoán.
    *   Hệ thống tính toán `Prediction Error` cho cả hai.
    *   Synapse Rắn vẫn nắm quyền kiểm soát hành động (Control Authority). Synapse Bóng ma chỉ chạy ngầm.

*   **Bước 3: Đảo chính (The Coup):**
    *   Nếu trong cửa sổ thời gian $T$, Synapse Bóng ma dự đoán chính xác hơn Synapse Rắn liên tục (vượt qua `Superiority Threshold`):
    *   **Action:**
        1.  **Revoke** Synapse Rắn (Biến nó thành Rác).
        2.  **Promote** Synapse Bóng ma thành Synapse chính thức (nhưng vẫn ở trạng thái Fluid để kiểm định thêm, hoặc Solid ngay nếu độ tin cậy cực cao).
    *   **Log:** "Agent đã thay thế niềm tin cũ bằng tri thức xã hội mới."

*   **Kết luận:** Cơ chế này cho phép Agent "Mở lòng" (Open-minded) nhưng "Thận trọng" (Skeptical). Nó chỉ thay đổi khi cái mới thực sự được chứng minh là tốt hơn cái cũ thông qua thực nghiệm (Empirical Evidence).

---

## 2. Xung đột: Vector Spike (Không gian) vs. STDP (Thời gian)

### 2.1 Bản chất Xung đột
*   **STDP (Cổ điển):** Chỉ thay đổi độ lớn trọng số vô hướng $w$ dựa trên $\Delta t$. SNN nhị phân (0/1) không quan tâm "nội dung" xung.
*   **Vector Spike:** Xung mang thông tin hướng không gian (Vector 16 chiều). Hai xung đến cùng lúc ($\Delta t = 0$, lý tưởng cho STDP) nhưng Vector nội dung khác nhau hoàn toàn (ví dụ: Vector "Đỏ" và Vector "Xanh").
*   **Vấn đề:** Nếu ta chỉ dùng STDP truyền thống, ta sẽ tăng trọng số cho cả những kết nối sai lệch về nội dung. Neuron sẽ học được "Khi nào" bắn, nhưng không học được "Bắn vào cái gì".

### 2.2 Giải pháp: Tách biệt Học Không-Thời gian (Spatiotemporal Decoupling)

Chúng ta tách quá trình học làm 2 quy trình song song tác động lên 2 thành phần khác nhau của Neuron.

1.  **Học Không gian (Spatial Learning - "What to fire at"):**
    *   **Đối tượng:** `Prototype Vector` (Vector Mẫu của Neuron).
    *   **Thuật toán:** Unsupervised Clustering (Kohonen / Oja's Rule).
    *   **Logic:** Khi Neuron bắn (nghĩa là nó đã nhận diện được một mẫu), nó xoay nhẹ `Prototype Vector` của mình về phía trung bình cộng của các Vector input vừa kích hoạt nó.
    *   $$\Delta \vec{P} = \eta_{space} \cdot (\vec{V}_{input} - \vec{P})$$
    *   *Kết quả:* Neuron tự tinh chỉnh "Gu" thẩm mỹ của mình để khớp với dữ liệu thực tế.

2.  **Học Thời gian (Temporal Learning - "When to fire"):**
    *   **Đối tượng:** Scalar Weights $w_{ij}$ của Synapse.
    *   **Thuật toán:** STDP 3 yếu tố (như đã thiết kế).
    *   **Logic:** Nếu Input A (dù vector gì) luôn xuất hiện trước khi Neuron B bắn -> Tăng trọng số $w_{AB}$.
    *   *Lưu ý:* Trọng số $w$ bây giờ đóng vai trò là "Độ tin cậy nhân quả" (Causal Trustworthiness), không phải là bộ lọc nội dung.

*   **Cơ chế Kích hoạt Tổng hợp:**
    *   Input $i$: Vector $\vec{x}_i$, Trọng số $w_i$.
    *   Đầu vào hiệu dụng (Effective Input) = $\text{Cosine}(\vec{x}_i, \vec{P}) \times w_i$.
    *   *Nghĩa là:* Tín hiệu chỉ mạnh khi nó vừa **Giống Mẫu** (Spatial Match) vừa đến từ nguồn **Tin cậy** (Temporal Match).

---

## 3. Xung đột: Bùng nổ Tham số (Hyperparameter Chaos)

### 3.1 Bản chất Xung đột
Hệ thống hiện tại có quá nhiều "Magic Numbers":
*   $\tau$ (STDP decay), $\eta$ (Learning rate), $\theta$ (Threshold base), $\beta$ (Homeostasis rate), $T_{commit}$ (Commit time), $E_{tol}$ (Error tolerance)...
*   **Vấn đề:** Chỉ cần sai một số, hệ thống sụp đổ (Động kinh hoặc Chết). Việc tinh chỉnh tay (Manual Tuning) là bất khả thi với mạng lớn và môi trường động.

### 3.2 Giải pháp: Meta-Homeostasis (Cân bằng Nội môi Bậc cao)

Thay vì cố tìm giá trị cố định cho các tham số (`Threshold = 1.0`), ta định nghĩa **Mục tiêu Vận hành (Operational Objectives)** và để hệ thống tự điều chỉnh tham số để đạt mục tiêu đó (PID Controller).

**Bảng Quy tắc Meta-Control:**

| Tham số cần chỉnh (Knob) | Mục tiêu Điều khiển (Target Objective) | Cơ chế Feedback (PID) |
| :--- | :--- | :--- |
| **Threshold ($\theta$)** | **Global Firing Rate:** Giữ ở mức ~1-2%. | Firing > 2% -> Tăng $\theta$. Firing < 0.5% -> Giảm $\theta$. |
| **Inhibition Strength** | **Epilepsy Score:** Giữ < 0.5. | Score cao -> Tăng Ức chế. |
| **Learning Rate ($\eta$)** | **Prediction Error:** Giữ Error giảm dần. | Error cao đột ngột (Ngạc nhiên) -> Tăng $\eta$ (Học nhanh). Error thấp và ổn định -> Giảm $\eta$ (Học chậm/Tinh chỉnh). |
| **Commit Threshold** | **Commit Rate:** Giữ % Neuron Solid ~50-70%. | Quá ít Solid -> Giảm ngưỡng cam kết. Quá nhiều Solid (bão hòa) -> Tăng ngưỡng. |

*   **Kết luận:** Chúng ta chuyển bài toán từ "Tìm tham số đúng" (rất khó) sang "Tìm trạng thái cân bằng đúng" (dễ hơn và tự nhiên hơn). Hệ thống sẽ tự tìm ra các tham số cục bộ phù hợp cho từng vùng não tại từng thời điểm.
