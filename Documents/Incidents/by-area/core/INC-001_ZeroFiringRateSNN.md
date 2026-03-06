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
2. Sau khi gọi reset chuyển sang `Episode 1`, toàn bộ 1024 nơ-ron rơi vào trạng thái "nghỉ trơ" (Refractory Period) vĩnh viễn và không bao giờ phục hồi. Hệ số phát xung trung bình (`avg_firing_rate`) báo hỏng ở mức 0.0 theo suốt toàn bộ vòng đời ứng dụng sau đó.
3. Kênh phân bổ tín hiệu vào SNN (Input Encoding) khi chẩn đoán cũng cho thấy chỉ 16 nơ-ron đầu tiên nhận được xung thay vì toàn bộ mảng.

---

## 4. Root Cause (Căn nguyên)

### 4.1. Phân tích Vi mô (Micro Analysis - @integrative-critical-analysis)
**Sai lầm trong logic/Code:**
- **Lỗi ánh xạ mã hóa (Input Encoding):** Cách mã hóa cũ cố tình nhồi nhét `pots[:16] = sensor_vector` mà bỏ qua 1008 nơ-ron còn lại. Sai lầm tư duy ở đây là xem biến "kích thước vector không gian" bằng với kích thước của hệ thần kinh, tạo nên sự đứt gãy.
- **Lỗi tràn bộ đệm SNN:** Ở cấp độ Python, `RLAgent.reset()` đã khởi tạo lại đối tượng SNN context giữa mỗi hiệp, nhưng nó lại bỏ sót không giải phóng các tensors Numpy thô (raw math tensors) trong `domain_ctx.heavy_tensors` - vốn chứa `last_fire_times` và `potentials`.
*Tại sao tư duy code lại sai?* Người viết code đã lầm tưởng rằng cơ chế garbage collector của Python hoặc hàm reset tổng của hệ thống Theus sẽ tự động can thiệp dọn sạch giá trị tĩnh trong `heavy_tensors`, mà quên mất POP Data Context trong Theus phải được thao tác trực tiếp và dọn dẹp tường minh.

### 4.2. Phân tích Vĩ mô (Macro Analysis - @systems-thinking-engine)
**Tradeoff kiến trúc và Vòng lặp phản hồi:**
- Lỗi này thực chất bộc lộ xung đột cơ bản trong việc "Tối ưu hóa bộ nhớ" (Memory Optimization) vs "Quản lý Vòng đời" (Lifecycle Management). Theus sử dụng cấu trúc `heavy_tensors` để mô phỏng vector POP và zero-copy với Rust nhằm đạt tốc độ cực cao. Kết cấu này nằm ngoài vòng đời quản lý Garbage Collector tiêu chuẩn của lớp OOP bao bọc (Wrapper).
- Vòng lặp phản hồi hỏng: Các nơ-ron "ghi nhớ" thời gian phát xung (last_fire_times) là 1000ms ở môi trường mô phỏng. Khi qua tập mới, time_step quay về 0ms. Nơ-ron hiểu rằng nó vừa mới phát xung (trong tương lai/quá khứ vô cực) và tự động rơi vào chu trình "Global Refractory Period" hãm không cho phát nữa.

---

## 5. Impact (Mức độ ảnh hưởng)
- **Ai/Cái gì bị ảnh hưởng:** Toàn bộ hệ thống RL_Agent, quy trình Theus Engine `run_experiments.py`.
- **Mức độ (Severity):** HIGH. SNN là trái lõi thuật toán thứ 2 trong hệ thống. Việc không có firing_rate biến EmotionAgent trở thành một Q-Learning Agent tầm thường, loại bỏ hoàn toàn tính toán sinh học. Ngoài ra, việc lưu trữ mảng Numpy không reset đe dọa sự ổn định dữ liệu và tràn RAM.

## 6. Resolution (Khắc phục)
1. **Khôi phục Vòng đời (Reset Tensors Vector):** Xóa trắng dữ liệu mảng Numpy `heavy_tensors` một cách tường minh mỗi khi Agent bắt đầu một vòng lặp sự kiện mới (`episode`). Đặt `last_fire_times` về `-1000`.
2. **Khuếch đại độ tương đồng:** Đổi cơ chế truyền SNN sang "Prototype Similarity Projection" (chiếu tín hiệu chéo dựa trên nguyên mẫu ngữ nghĩa) kết hợp hàm nén lập phương `sim ** 3`. Điều này giúp phủ bức xạ sensor lên toàn bộ 1024 nơ-ron thay vì 16.
3. **Ức chế toàn cầu (Global Inhibition):** Cài đặt yếu tố `norm_factor` tại vòng lặp `integrate` nhằm tự động co thắt dòng điện thế nếu có quá nhiều nơ-ron cùng "kích động" cùng 1 lúc (chống bão hòa tín hiệu).
4. **Nới lỏng Timeout Theus:** Gán trực tiếp `write_timeout_ms = 50000` cho bộ máy `TheusEngine` ở lệnh tạo cốt lõi để bảo chứng mô phỏng thời gian lớn hơn 30s.

## 7. Fixed In (Fix tại đâu)
- `src/agents/rl_agent.py` (Cải tổ vòng đời `reset()` của heavy_tensors)
- `src/processes/snn_rl_bridge.py` (Thuật toán Input Projection mới)
- `src/processes/snn_core_theus.py` (Thuật toán Local & Global Inhibition)
- `run_experiments.py` (Cấu hình `write_timeout_ms=50000`)

---

## 8. Comprehensive Analysis & Resolution Plan

### 8.1. Ethical & Epistemic Audit (@intellectual-virtue-auditor)
- **Humility (Khiêm tốn):** Có phải chúng ta đã chắp vá vội vàng? Ban đầu đúng là có, khi chỉ nghĩ việc `firing rate = 0` là một lỗi cấu hình hệ số amplification. May mắn là việc truy dò memory đã tiết lộ nguồn cơn của Heavy Tensors. Ta không quá tự mãn vào suy luận đầu tiên.
- **Courage (Dũng khí):** Chịu đối mặt với cơ chế POP vector. Khắc phục tensor thô thay vì bọc lại nó bằng OOP (cái sẽ làm mất đi tinh thần framework theus).
- **Integrity (Chính trực):** Khi thiết lập mảng chiếu prototype tương tự hóa `sim ** 3`, ta ghi nhận rằng điều này làm phức tạp thêm đồ thị code một tí thay vì nhét trực tiếp. Nhưng đó là nguyên tắc của SNN, nên ta tuân thủ nguyên bản độ thật của nơ-ron.

### 8.2. Giải pháp kế hoạch tổng quan
- **Immediate Fix (Băng cá nhân):** Bổ sung mảng `.fill(0)` nhanh vào `RLAgent.reset()`. Đã thực hiện.
- **Structural Fix (Liệu trình chữa trị):** Khởi tạo lại một phương pháp giao tiếp Input SNN (cosine similarity - prototype) để bảo đảm 1024 nơ-ron đều được làm việc một cách thưa thớt (sparse), cùng với logic tự chế ức chế ồ ạt cục bộ. Đã thực hiện và xác nhận thành công ổn định (`avg_firing_rate = 0.0018~`).
- **Process Fix (Vắc-xin):** Thêm một lớp Linter hoặc bộ test tự động (tương lai) quét qua Theus process để bảo đảm tất cả `domain.heavy_tensors` phải được khởi tạo lại ở hàm reset nếu được tái sử dụng trong vòng lặp liên tục, thay vì ngầm định. Cấu hình theus engine app-level cũng sẽ được cảnh báo tốt hơn về giới hạn `timeout` ở quy mô đa tác tử mảng lớn.
