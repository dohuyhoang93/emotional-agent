# Chương 03: Phương pháp & Kiến trúc (Methodology & Approach) - Revised

---

## 3.1 Triết lý Theus POP (Process-Oriented Programming)

Hệ thống được xây dựng trên nền tảng **Theus Framework**, tuân thủ nghiêm ngặt 3 nguyên lý vàng của kiến trúc Hướng Quy trình:

1.  **Dữ liệu "Câm" (Passive Data):** Các `Neuron`, `Synapse` hoàn toàn không có phương thức (method). Không có `neuron.fire()`. Dữ liệu chỉ là các Structs/Records nằm im trong Context.
2.  **Quy trình Thuần túy (Pure Processes):** Mọi logic (tích phân, bắn xung, học) nằm trong hàm.
    *   `process_integrate(neurons, signals) -> new_neurons`
    *   Hàm này nhận data, trả về data mới, không có side-effect ẩn.
3.  **Điều phối bằng Cấu hình (Config-Driven):** Thứ tự chạy các Process định nghĩa trong YAML, cho phép thay đổi logic luồng mà không sửa code Python.

## 3.2 Ảo hóa Neuron: Tại sao ECS thắng OOP?

Để vận hành 1 triệu neuron trên PC, sự khác biệt giữa ECS và OOP là sống còn.

### Mô hình OOP (Cổ điển - Sai lầm)
Mỗi neuron là một Python Object. Tốn 64 bytes overhead. Cache Miss liên tục vì dữ liệu nằm rải rác trong Heap.

### Mô hình ECS (Data-Oriented - Chính xác)
Neuron chỉ là một chỉ số (Index) trong các mảng dữ liệu lớn (`potentials`, `thresholds`, `vectors`).
*   **Lợi ích:**
    1.  **Cache Locality:** Dữ liệu liền mạch -> Tốc độ tăng 10-50 lần.
    2.  **SIMD:** Các phép toán Vector diễn ra song song (AVX512).

---

## 3.3 Kiến trúc Lai: SNN-RL Gated Integration
**(Phản hồi cho vấn đề "Information Bottleneck")**

Chúng ta từ bỏ mô hình "Chưng cất vô hướng" (Scalar Distillation) ngây thơ. Thay vào đó, chúng ta sử dụng mô hình **Tích hợp Cổng Phi tuyến (Non-linear Gated Integration)**.

### 3.3.1 SNN không còn là "GPU Cảm xúc" đơn thuần
SNN đóng vai trò là **Bộ trích xuất Đặc trưng Ngữ nghĩa theo Thời gian thực (Semantic Feature Extractor)**.

*   **Logic:** RL Agent (DQN/PPO).
*   **Cảm xúc:** SNN Engine.
*   **Giao diện:**
    *   Thay vì gửi `Fear=0.8`.
    *   SNN gửi **Semantic Vector**: $V_{emo} \in \mathbb{R}^{16}$. (Ví dụ: [0.8, 0.1, 0.0, ... 0.9]).
    *   Vector này đại diện cho *Trạng thái Cảm xúc Phức hợp* (vừa sợ hãi, vừa tò mò, vừa đói).

### 3.3.2 Cơ chế Tích hợp (The Integration Formula)
RL Network nhận input $S_{total}$ là sự kết hợp của Quan sát Visua ($O_{vis}$) và Cảm xúc ($V_{emo}$).

Không dùng cộng tuyến tính. Sử dụng **Gating Network**:

$$H_{combined} = \text{ReLU}(W_v \cdot O_{vis} + W_e \cdot V_{emo} + b)$$
$$Q(s, a) = \text{Head}_{action}(H_{combined})$$

*   *Ý nghĩa:* Mạng RL tự học cách dùng cảm xúc.
    *   Có lúc nó dùng Fear để *nhân* với Reward (ức chế).
    *   Có lúc nó dùng Fear như một *feature* để nhận diện kẻ thù ("Nếu thấy Đỏ A VÀ Sợ -> Chạy").
    *   => Không mất thông tin, không gò bó tuyến tính.

---

## 3.4 Động cơ Hướng Sự kiện (Event-Driven Engine)

Để tiết kiệm năng lượng, áp dụng "Lazy Evaluation".

*   **Lazy Leak:**
    *   Chỉ tính cập nhật rò rỉ khi neuron nhận xung mới.
    *   $V_{now} = V_{old} \cdot \text{decay}^{\Delta t}$.
*   **Giải pháp Drift (Resync):**
    *   Để khắc phục sai số tích lũy của công thức Lazy Leak (đã được cảnh báo), hệ thống có luồng **Periodic Resync** chạy ngầm mỗi 1000ms để tính toán lại chính xác toàn bộ trạng thái mạng.
