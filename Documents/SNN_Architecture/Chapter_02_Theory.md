# Chương 02: Cơ sở Lý thuyết (Theoretical Core) - Expanded

---

## 2.1 Hebbian Learning Hiện đại (Updated 2025)

Cơ chế cốt lõi của hệ thống không phải là Lan truyền ngược (Backpropagation), mà là **Học Hebbian (Hebbian Learning)**, cụ thể là phiên bản điều biến bởi phần thưởng (Reward-modulated).

### 2.1.1 Toán học của STDP (Spike-Timing-Dependent Plasticity)

Quy tắc STDP xác định sự thay đổi trọng số $\Delta w$ dựa trên khoảng thời gian $\Delta t = t_{post} - t_{pre}$ (thời điểm neuron sau trừ neuron trước).

**Công thức Cập nhật Trọng số Cơ bản:**

$$
\Delta w(\Delta t) = \begin{cases} 
A_+ \cdot \exp\left(-\frac{\Delta t}{\tau_+}\right) & \text{if } \Delta t > 0 \text{ (Causal: LTP)} \\
-A_- \cdot \exp\left(\frac{\Delta t}{\tau_-}\right) & \text{if } \Delta t < 0 \text{ (Acausal: LTD)}
\end{cases}
$$

Trong đó:
*   $A_+, A_-$: Biên độ học cực đại (Learning rate) cho tăng/giảm.
*   $\tau_+, \tau_-$: Hằng số thời gian phân rã (Decay time constant), thường khoảng 10-20ms.
*   **Ý nghĩa:** Nếu A bắn ngay trước B ($\Delta t \approx 0^+$), liên kết tăng cực mạnh. Nếu A bắn quá xa hoặc bắn sau B, liên kết giảm.

### 2.1.2 Quy tắc 3 Yếu tố (Three-Factor Rules: R-STDP)

STDP cơ bản là mù quáng (Unsupervised). Để hướng dẫn Agent học hành vi có ích, ta nhân thêm yếu tố thứ 3 là **Dopamine ($D$)**.

**Công thức R-STDP:**

$$
\frac{dw}{dt} = \eta \cdot \text{STDP}(\Delta t) \cdot D(t)
$$

Trong đó:
*   $\text{STDP}(\Delta t)$: "Vết hằn ký ức" (Eligibility Trace). Nó lưu lại dấu vết rằng "A và B vừa hoạt động cùng nhau", nhưng chưa thay đổi trọng số ngay.
*   $D(t)$: Tín hiệu Dopamine toàn cục nhận được từ môi trường (Reward - Baseline).
*   **Cơ chế hoạt động:**
    1.  Agent thử hành động: Thấy lửa (A) -> Chạm vào (B).
    2.  Hệ thống tạo vết hằn (Trace) cho liên kết A->B.
    3.  Môi trường trả về: Đau quá! ($D(t) < 0$).
    4.  Cập nhật: $\Delta w = \text{Positive Trace} \times \text{Negative Dopamine} = \text{Negative Change}$.
    5.  Kết quả: Trọng số A->B giảm mạnh. Lần sau thấy lửa sẽ ức chế hành động chạm.

## 2.2 Động lực học Neuron (Neuron Dynamics)

Chúng ta sử dụng mô hình **Leaky Integrate-and-Fire (LIF)** được đơn giản hóa cho tính toán số.

**Phương trình Điện thế màng ($V$):**

$$
V(t) = V(t-1) \cdot (1 - \lambda_{leak}) + \sum_{i} w_i \cdot S_i(t)
$$

*   $\lambda_{leak}$: Hệ số rò rỉ (ví dụ 0.1). Giúp neuron "quên" các kích thích cũ không quan trọng.
*   $S_i(t)$: Tín hiệu đầu vào từ neuron $i$ (chỉ xét các spike).

**Điều kiện Bắn xung:**
Nếu $V(t) \ge V_{th}$ (Ngưỡng):
1.  Phát tín hiệu Spike.
2.  $V(t) \leftarrow V_{reset}$ (Thường là 0).
3.  Vào trạng thái "Trơ" (Refractory) trong $T_{ref}$ giây.

## 2.3 Cân bằng Nội môi (Homeostasis - Adaptive Threshold)

Để tránh mạng bị "chết" hoặc "động kinh", ngưỡng $V_{th}$ không cố định mà tự thích nghi.

$$
V_{th}(t) = V_{th\_base} + \beta \cdot (R(t) - R_{target})
$$

*   $R(t)$: Tần số bắn trung bình (Firing Rate) của neuron gần đây.
*   $R_{target}$: Tần số mong muốn (ví dụ: 0.05 spike/step).
*   $\beta$: Hệ số thích nghi.
*   **Ý nghĩa:** Nếu neuron bắn quá nhiều ($R > R_{target}$), ngưỡng sẽ tăng lên để kìm hãm nó.

## 2.4 Logic Hình thức từ Cấu trúc Mạng (Emergent Logic)

Logic không được lập trình (`if/else`), mà nảy sinh từ cấu hình trọng số ($w$) và ngưỡng ($\theta$).

*   **Cổng AND ($A \land B$):**
    *   $w_A = 0.6, w_B = 0.6, \theta = 1.0$.
    *   Chỉ khi cả A và B cùng bắn, tổng $V = 1.2 > 1.0$, neuron đầu ra mới bắn.
*   **Cổng OR ($A \lor B$):**
    *   $w_A = 1.2, w_B = 1.2, \theta = 1.0$.
    *   Chỉ cần A hoặc B bắn là đủ kích hoạt.
*   **Cổng NOT ($\neg A$):**
    *   Neuron ức chế có $w_{inh} = -10.0$.
    *   Khi nó bắn, nó lập tức dập tắt neuron đích.
