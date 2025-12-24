# Chương 06: Phân tích Rủi ro & Vận hành (Failure Analysis & Operations) - Consolidated

Cẩm nang "Cấp cứu" và vận hành hệ thống ổn định lâu dài.

---

## 6.1 Các Chỉ số Sức khỏe (Health Metrics)

### 6.1.1 Chỉ số Sinh tồn
1.  **Global Firing Rate:**
    *   An toàn: 0.5% - 5%.
    *   Chết: < 0.1%.
    *   Động kinh: > 20%.
2.  **Epilepsy Score:** Đo mức độ đồng bộ hóa nguy hiểm của mạng.

### 6.1.2 Chỉ số Học tập
*   **Dopamine Average:** Nếu thấp kéo dài -> Agent bị trầm cảm (Learned Helplessness).
*   **Commitment Rate:** Tỷ lệ % neuron đã ở trạng thái SOLID.

---

## 6.2 Giao thức Tự động Phục hồi (Automated Recovery)

### Protocol A: Chống Động kinh (Anti-Epilepsy)
*   **Trigger:** Firing Rate > 20%.
*   **Action:** Hard Reset điện thế + Bơm ức chế toàn cục (Global Inhibition).

### Protocol B: Kích tim (Resuscitation)
*   **Trigger:** Firing Rate < 0.01% (Chết lâm sàng).
*   **Action:** Bơm nhiễu Poisson (Noise Injection) vào lớp Input.

### Protocol C: Cân bằng Synapse (Scaling)
*   **Trigger:** Trọng số bị bão hòa.
*   **Action:** Nhân tất cả trọng số với 0.8.

---

## 6.3 Rủi ro Xã hội (Social Stability)

### 6.3.1 Hiệu ứng Buồng Vang (Echo Chamber)
*   *Rủi ro:* Lan truyền tri thức sai lệch toàn quần thể.
*   *Giải pháp:* Duy trì 10% Agent **"Contrarian"** (Chống đối) để bảo tồn sự đa dạng di truyền.

### 6.3.2 Sụp đổ Mỏ neo (Anchor Collapse)
*   *Giải pháp:* **Conservative Plasticity**. Ancestor chỉ cập nhật khi có đồng thuận lớn (>80%).

---

## 6.4 Meta-Homeostasis (Cân bằng Nội môi Bậc cao)

Giải quyết vấn đề **Bùng nổ Tham số (Parameter Chaos)**. Thay vì chỉnh tay (Manual Tuning), hệ thống tự điều chỉnh.

**Cơ chế PID Control:**

| Tham số (Knob) | Mục tiêu (Target) | Logic Điều khiển |
| :--- | :--- | :--- |
| **Threshold ($\theta$)** | **Global Firing Rate** (1.5%) | Rate tăng -> Tăng $\theta$. Rate giảm -> Giảm $\theta$. |
| **Inhibition ($I_{inh}$)** | **Epilepsy Score** (< 0.5) | Score tăng -> Tăng $I_{inh}$. |
| **Learning Rate ($\eta$)** | **Prediction Error** (Giảm dần) | Error tăng đột ngột (Ngạc nhiên) -> Tăng $\eta$ (Học nhanh). |
| **Commit Threshold** | **Commit Rate** (~60%) | Quá ít Solid -> Giảm ngưỡng cam kết. |

Hệ thống hoạt động như một bộ điều nhiệt (Thermostat) tự động, duy trì trạng thái "Critically Stable" (Cân bằng tới hạn) để tối ưu hóa khả năng thính nghi.
