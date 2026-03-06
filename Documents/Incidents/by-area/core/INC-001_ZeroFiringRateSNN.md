---
id: INC-001
title: Zero Firing Rate in SNN
area: core
severity: High
status: resolved
---

# Incident Report: INC-001 - Lỗi Tỉ lệ Firing Rate Mạng SNN Tụt Về 0.0

## 1. Summary (Tóm tắt)
Mạng Spiking Neural Network (SNN) đóng vai trò nạp "cảm xúc" / "ngữ cảnh nội sinh" cho module RL_Agent đã gặp vấn đề nghiêm trọng: `avg_firing_rate` giảm dốc về `0.0` ngay sau tập (episode) đầu tiên khi chạy trên tiến trình đa tác tử (`run_experiments.py`). Sự cố này khiến RL_Agent bị mù cảm xúc, làm mất đi sự kết nối Theus/POP giữa tri nhận và hành vi.

## 2. Background (Bối cảnh)
Hệ thống EmotionAgent kết hợp RL (Reinforcement Learning) và SNN. 
Mỗi step, *sensor_vector* truyền vào một tập hợp tín hiệu tri nhận để chuyển đổi thành điện thế mạng (potentials) giúp các nơ-ron phát xung (spikes). Những xung này sau đó được ánh xạ thành các yếu tố cảm nhận ảnh hưởng đến quyết định của Q-Learning. Môi trường kiểm thử chứa 5 agents chạy trong không gian phức tạp.

## 3. What Went Wrong (Điều gì đã xảy ra)
1. Trong tập `Episode 0`, SNN hoạt động cục bộ ban đầu.
2. Sau khi gọi reset chuyển sang `Episode 1`, toàn bộ 1024 nơ-ron rơi vào trạng thái đóng băng vĩnh viễn. Hệ số phát xung trung bình (`avg_firing_rate`) báo hỏng ở mức 0.0 theo suốt toàn bộ vòng đời ứng dụng sau đó.
3. Kênh phân bổ tín hiệu vào SNN (Input Encoding) khi chẩn đoán cũng cho thấy chỉ một phần nhỏ nơ-ron nhận được xung, không đủ để duy trì hoạt động mạng lớn.

---

## 4. Root Cause (Căn nguyên)

### 4.1. Phân tích Kỹ thuật (Technical Analysis)
**Căn nguyên thực sự được xác định qua 3 lớp lỗi chồng chéo:**

1.  **Lỗi Tỉ lệ (Scaling Failure - snn_rl_bridge.py):** Cơ chế mã hóa cũ giới hạn `receptor_count` ở mức tối đa 64. Đối với mạng 1024 nơ-ron, mật độ 6% là quá thấp để duy trì chuỗi phản ứng dây chuyền, dẫn đến tín hiệu bị dập tắt ngay từ lớp vỏ.
2.  **Lỗi Ức chế Toàn cầu (Excessive Normalization - snn_core_theus.py):** Hệ số `norm_factor` trong quá trình tích hợp (`process_integrate`) được tính toán quá tích cực, vô tình triệt tiêu toàn bộ điện thế khi số lượng nơ-ron lớn, ngăn cản việc tích lũy để vượt ngưỡng.
3.  **Lỗi Rò rỉ Trạng thái (State Leakage - rl_agent.py):** Mặc dù các đối tượng được reset, nhưng **PID Controller State** (`pid_integral`, `pid_prev_error`) và mảng **Thresholds** trong `heavy_tensors` bị giữ lại giá trị của Episode 0. Do Episode 0 thường kết thúc với ngưỡng cao (để kiềm chế spike), Episode 1 bắt đầu với "rào cản" quá lớn khiến mạng bị đóng băng ngay lập tức.

### 4.2. Phân tích Hệ thống (@systems-thinking-engine)
**Xung đột giữa Hiệu suất (Performance) và Tính Đồng nhất (Consistency):**
Việc sử dụng `heavy_tensors` (Zero-copy Numpy buffers) giúp tăng tốc độ xử lý hàng trăm lần nhưng tạo ra một "vùng xám" trong quản lý vòng đời. Hệ thống `Theus Engine` ưu tiên tính ổn định của Tensor để tránh cấp phát lại (Allocation), nhưng logic RL_Agent lại yêu cầu tính sạch sẽ tuyệt đối giữa các episodes. Sự đứt gãy trong giao thức Reset chính là điểm yếu hệ thống.

---

## 5. Impact (Mức độ ảnh hưởng)
- **Cơ chế:** SNN bị đóng băng hoàn toàn sau episode đầu tiên.
- **Mức độ (Severity):** HIGH. Toàn bộ hệ thống Multi-Agent bị mất khả năng học tập ngữ cảnh cảm xúc, chỉ còn vận hành như một bộ Q-Learning cơ bản.

## 6. Resolution (Khắc phục)

1.  **Scaling Topology (snn_rl_bridge.py):** Chuyển đổi `receptor_count` sang tỉ lệ động `max(16, int(N * 0.2))`. Việc đảm bảo 20% mạng lưới nhận tín hiệu trực tiếp giúp duy trì sự lan truyền xung mạnh mẽ hơn ở quy mô lớn.
2.  **Proportional Normalization (snn_core_theus.py):** Điều chỉnh `norm_factor` tỉ lệ thuận với kích thước mạng, cho phép tích hợp xung linh hoạt hơn mà không gây ra hiện tượng "co giật" mạng (seizure).
3.  **Explicit Lifecycle Reset (rl_agent.py):** Bổ sung logic dọn dẹp triệt để trong `RLAgent.reset()`:
    - Đặt lại mảng `thresholds` về giá trị `initial_threshold` ban đầu.
    - Xóa trắng integral và error của bộ điều khiển PID trong `pid_state`.
    - Reset toàn bộ `heavy_tensors` liên quan đến `last_fire_times` và `firing_traces`.
4.  **Dynamic Topological Receptors:** Loại bỏ logic `sim ** 3` cũ, thay bằng cơ chế ánh xạ Topological kết hợp với **Sensory Adaptation** (tăng độ nhạy khi mạng tĩnh lặng và ngược lại).
5.  **Timeout Adjustment**: Tăng `write_timeout_ms` lên 50000ms trong `run_experiments.py` để phù hợp với độ phức tạp của môi trường Maze.

## 7. Verification (Nghiệm chứng)
Sau khi áp dụng các bản vá, kết quả chạy thử nghiệm phức tạp (`experiments.json`) cho thấy:
- **Firing Rate khôi phục:** `avg_firing_rate` đạt mức ổn định ~`0.00025` (tương đương 130 spikes/episode).
- **Tính ổn định:** Tỉ lệ này được duy trì nhất quán qua Episode 1, 2, 5, 7... mà không còn bị sụp đổ về 0.0.
- **Tính phản hồi:** Ngưỡng nơ-ron và điện thế biến thiên linh hoạt theo tín hiệu cảm biến từ môi trường Maze.

## 8. Fixed In (Fix tại đâu)
- `src/agents/rl_agent.py` (Reset PID & Tensors)
- `src/processes/snn_rl_bridge.py` (Scaling Receptors & Dynamic Sensitivity)
- `src/processes/snn_core_theus.py` (Proportional Inhibition)
- `run_experiments.py` (Timeout & Config Overrides)

---

## 9. Bài học kinh nghiệm (Post-Mortem)
1. **Implicit vs Explicit**: Không bao giờ giả định các cấu trúc dữ liệu thô (tensors) sẽ tự động reset. Mọi trạng thái tồn tại lâu dài (persistent state) trong POP Data Context phải có giao thức reset tường minh.
2. **Dimension Awareness**: Các hằng số (như 64 receptors) thường phản ánh giới hạn tư duy tại thời điểm viết code cho mạng nhỏ. Mọi logic xử lý mảng phải được viết dưới dạng Dynamic Scaling ngay từ đầu.
3. **PID Windup Risk**: Trạng thái tích lũy sai số (Integral) là mục tiêu hàng đầu cần kiểm tra khi hệ thống bị treo hoặc bão hòa sau một chu kỳ làm việc.
