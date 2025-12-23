# Chương 06: Phân tích Rủi ro & Vận hành (Failure Analysis & Operations) - Expanded

Xây dựng SNN không khó, vận hành nó ổn định mới khó. Chương này cung cấp cẩm nang "Cấp cứu" (Troubleshooting) cho hệ thống.

---

## 6.1 Các Chỉ số Sức khỏe (Health Metrics)

Hệ thống cần export các metric sau ra Dashboard (hoặc Log file) mỗi giây.

### 6.1.1 Chỉ số Sinh tồn (Survival Metrics)
1.  **Global Fire Rate ($F_{rate}$):** Tỷ lệ % neuron bắn xung trong 1 giây.
    *   *Bình thường:* 0.5% - 5%.
    *   *Cảnh báo (Chết):* < 0.1%. (Hệ thống đang ngủ đông hoặc ngưỡng quá cao).
    *   *Nguy hiểm (Động kinh):* > 20%. (Hệ thống quá nhạy cảm, sắp tràn RAM).
2.  **Epilepsy Score (Điểm Động kinh):** Đo lường sự đồng bộ hóa nguy hiểm.
    *   Công thức: Tỷ lệ phương sai của hoạt động quần thể so với tổng phương sai cá nhân.
    *   Nếu score > 0.8: Mạng đang dao động đồng bộ (Synchronized Oscillation). Cần phá vỡ bằng nhiễu (Jitter).

### 6.1.2 Chỉ số Học tập (Learning Metrics)
1.  **LTP/LTD Ratio:** Tỷ lệ giữa số lượng Synapse được tăng trọng số (LTP) và giảm trọng số (LTD).
    *   *Lý tưởng:* ~1.0 (Cân bằng).
    *   *Rủi ro:* Nếu LTP >> LTD, mạng sẽ bão hòa (tất cả weight = max). Nếu LTD >> LTP, mạng sẽ mất kết nối.
2.  **Dopamine Average:** Giá trị trung bình của tín hiệu Reward trong cửa sổ 1000 bước.
    *   Nếu luôn < 0: Agent đang rơi vào trạng thái "Bất lực tập nhiễm" (Learned Helplessness).

## 6.2 Giao thức Tự động Phục hồi (Automated Recovery Protocols)

Đừng để con người phải can thiệp. Hệ thống phải có **Circuit Breakers (Cầu dao tự động)**.

### Protocol A: Chống Động kinh (Anti-Epilepsy)
*   **Trigger:** Khi $F_{rate} > 20\%$ trong 100ms liên tục.
*   **Action:**
    1.  **Hard Reset:** Set toàn bộ $V_{potential} = 0$ cho tất cả neuron ngay lập tức.
    2.  **Global Inhibition:** Bơm một dòng điện ức chế ($I_{inh} = -5.0$) vào toàn mạng trong 50ms tiếp theo.
    3.  **Threshold Boost:** Tăng ngưỡng kích hoạt cơ bản ($V_{th\_base}$) lên 10%.

### Protocol B: Kích tim (Resuscitation)
*   **Trigger:** Khi $F_{rate} < 0.01\%$ trong 1000ms (1 giây yên lặng).
*   **Action:**
    1.  **Noise Injection:** Bơm dòng điện ngẫu nhiên Poisson vào 10% neuron Input để "mồi" lại hoạt động.
    2.  **Threshold Decay:** Giảm ngưỡng kích hoạt cơ bản xuống 5%.
    3.  *Ghi chú:* Đây là cách não bộ mơ (Dreaming) khi thiếu kích thích giác quan.

### Protocol C: Cân bằng Synapse (Homeostatic Scaling)
*   **Trigger:** Khi `Average_Weight` > 0.9 * `Max_Weight` (Bão hòa).
*   **Action:**
    1.  **Multiplicative Scaling:** Nhân tất cả trọng số $W_{ij}$ với một hệ số $k = 0.8$.
    2.  Việc này giữ nguyên tỷ lệ tương đối giữa các synapse (ký ức không bị mất) nhưng đưa mạng về vùng hoạt động tuyến tính.

## 6.3 Chiến lược Debug & Visualization

Chúng ta không thể `print(log)` cho 1 triệu neuron. Cần công cụ trực quan hóa (như fMRI cho máy tính).

### Bộ công cụ SNN-Vis (Cần xây dựng)
1.  **Macro-View (Cái nhìn tổng thể):**
    *   Biểu đồ Heatmap 2D: Trục X là Layer, Trục Y là Neuron ID.
    *   Pixel sáng lên khi Neuron bắn.
    *   *Mục đích:* Nhìn thấy "Sóng hoạt động" lan truyền từ Input -> Output.
2.  **Micro-View (Cái nhìn vi mô):**
    *   Chọn 1 neuron cụ thể.
    *   Vẽ đồ thị $V_{potential}(t)$ theo thời gian thực.
    *   Vẽ các Spike đến (Input Spikes) và Spike đi (Output Spike).
    *   *Mục đích:* Kiểm tra xem Neuron đó có tích hợp tín hiệu đúng công thức không.

### Nhật ký Tai nạn (Black Box Logs)
Khi hệ thống Crash hoặc Reset, phải dump ngay trạng thái ra file:
*   `crash_dump_{timestamp}.json`: Chứa phân bố trọng số (Histogram of Weights) và trạng thái 100ms cuối cùng của hàng đợi sự kiện.
*   Điều này giúp ta biết tại sao mạng bị bùng nổ (Do đầu vào quá lớn? Hay do feedback loop dương?).
