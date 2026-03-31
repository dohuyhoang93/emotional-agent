---
id: INC-006
title: Hybrid SNN-MLP Architecture Failure (Non-stationarity Cascade)
area: core
severity: Critical
status: resolved
---

# Incident Report: INC-006_HybridArchitectureFailure

## 1. Summary
Trong thử nghiệm `multi_agent_complex_maze`, mạng agent gồm kiến trúc lai SNN (Encoder) và MLP (DQN Actor) đã gặp hiện tượng sụp đổ hiệu suất học tập sau giai đoạn khám phá. Reward trung bình giảm dần về mức -212.55, Success Rate cực thấp (~1%), trong khi hàm Loss của MLP xuất hiện các gai nhiễu (Spike) tăng vọt lên tới 2403.48. SNN cũng hứng chịu tình trạng suy kiệt số lượng Synapse (mất 60%). Toàn bộ hệ thống mất phương hướng trong quá trình tìm lời giải.

## 2. Background
Hệ thống sử dụng Spiking Neural Network (SNN) làm bộ trích xuất đặc trưng (State Representation) và truyền đầu ra sang một module Multi-Layer Perceptron (MLP) đóng vai trò mạng giá trị (DQN) tính toán chính sách hành động. 
SNN được kích hoạt tính năng chọn lọc kiến trúc `use_neural_darwinism: true` thực hiện cắt tỉa các synapse yếu mỗi 500 bước (`darwinism_interval = 500`). 
Tuy nhiên, môi trường chứa các cấu trúc phức tạp như "Logical Switches" và "Dynamic Walls", đòi hỏi chuỗi hành động có tính logic liên tục cao mới vượt qua được.

## 3. What Went Wrong
Giai đoạn chuyển tiếp từ thám hiểm (exploration, epsilon cao) sang chắt lọc (exploitation, epsilon thấp) bị hỏng hoàn toàn.
- **SNN Pruning**: SNN thực hiện Neural Darwinism quá tay, số lượng synapse rơi từ 13,567 đầu chu kỳ xuống còn 5,249, khiến tín hiệu Firing Rate giảm và Homeostasis PID không thể chống đỡ được (vì cấu trúc vật lý mạng đã bị làm nghèo nàn).
- **MLP Gradient Explosion**: Mạng DQN không học được đúng định hướng, ước lượng Q-value vỡ nát (rớt xuống rất sâu vào mức âm -8.51). Loss liên tục có đột biến cực mạnh dẫn tới thông tin Gradient nổ hoặc không hội tụ.

## 4. Root Cause

### Micro Root Cause (Phân tích theo Integrative-Critical-Analysis / Virtue Auditing)
**Mental Model Error**: Các yếu tố "Sinh học mỏng" (Biological plausibility) như Neural Darwinism được coi là đương nhiên hiệu quả mà không tính đến độ trễ cần thiết cho việc học tập. Chúng ta giả định sai lầm (False Assumption) rằng "Cắt tỉa liên kết thì mô hình SNN sẽ chắt lọc được dữ liệu đầu vào tốt nhất cho MLP". Kết quả thực tế là SNN bị xén mất các cụm liên kết (sub-networks) có chức năng bộ nhớ truy xuất cho các tác vụ Logic Switches, khiến MLP phải tiếp nhận dữ liệu đầu vào rác hoặc bị nhiễu.

### Macro Root Cause (Phân tích theo Systems-Thinking-Engine)
**Structural Root Cause**: Mất nhất quán biểu diễn (Representational Consistency Flaw).
Hệ thống kết nối trực tiếp hai module khác biệt về nhịp sinh học: SNN cập nhật và tự phá hủy cấu trúc (mạng tĩnh không tồn tại) ghép nối thẳng với cấu trúc MLP dùng toán học hội tụ cực nghiêm ngặt vốn yêu cầu Distribution của Đầu vào phải ổn định theo thời gian (Markovian).
Mỗi 500 bước SNN cắt 60% synapse, tín hiệu đặc trưng (features vector) truyền vào MLP dịch chuyển đột ngột (Concept Drift). MLP bị ép phải học lại các phân bổ mới và thay đổi lại hầu hết các trọng số, phá vỡ tất cả những Q-values quý giá nào nó kịp nhận dạng ở 500 bước trước đó. Vòng lặp này (Reinforcing Loop) làm mọi thứ lụi tàn dần, kết hợp thêm độ trễ từ Môi trường động (Delay) khiến quá trình đổ sụp.

## 5. Impact
- **Mức độ ảnh hưởng**: Critical.
- Quá trình chạy thử nghiệm cho các bài toán quy mô cao hơn, có tính động (dynamic) sẽ hoàn toàn không thể học được bằng kiến trúc Hybrid hiện tại, làm tê liệt quá trình Scale-up của dự án EmotionAgent.

## 6. Resolution
**Đã được triển khai & Nghiệm chứng thành công (2026-03-30)**
Thay vì sử dụng bộ đệm toán học phi sinh học (EMA), lỗi Non-stationarity đã được dập tắt hoàn toàn bằng kiến trúc **Monotonic Additive Plasticity**:

1. **Bảo tồn Tuyệt đối Lịch sử và Đào thải Tĩnh lặng (Silent GC)**: Giữ nguyên khung xương SNN. Nếu Synapse bị STDP làm suy yếu (`Weight <= 0.001`), nó mới bị xóa vật lý. Không có bất kỳ cú sốc nào cho MLP. (Kết quả đo: Loss MLP giao động cực mượt `0.00x - 0.1` thay vì spike `2400` như cũ).
2. **Cổng Kép Chọn lọc Mọc Rễ (Dual-Gate Eligibility)**: Kết hợp Cổng 1 (ID Proximity) lọc O(1) và Cổng 2 (Cosine Similarity > 0.3) tại bán kính cụm hẹp. CPU hoạt động ổn định ở mức `2.5 steps/giây` cho mạng 1024-neurons. Mạng liên tục duy trì tốc độ mọc `~800-1000 synapses/episode` (Monotonic Growth).
3. **Giới hạn Sọ não Động (Dynamic Skull Limit)**: Chống tràn RAM bằng trần tỷ lệ thuận `MAX_SYNAPSES = int(N * (N - 1) * 0.3)` (~314k synapses cho mạng 1024). Bộ nhớ RAM hoàn toàn khóa chặt ở ngưỡng an toàn `~460 MB` xuyên suốt các episode.
4. **Resync Tensors Thông Minh**: Sử dụng `ensure_heavy_tensors_initialized` để rebuild các mảng Tensor khi có biến động sinh/diệt synapse, đảm bảo tính nhất quán (Consistency) hoàn hảo giữa Object và Numpy backend.

## 7. Fixed In
- Nâng cấp triệt để module `process_neural_darwinism` trong `src/processes/snn_advanced_features_theus.py`.
- Tinh chỉnh ghi nhận biến tích luỹ Spikes (`episode_total_spikes`) trong `src/processes/snn_core_theus.py` và `src/orchestrator/processes/p_enrich_metrics.py`.

## 8. Preventive Actions
- Viết kịch bản unit test đảm bảo phân bổ output tensor từ SNN không thay đổi quá `x%` mỗi khi Darwinism thực thi. Nếu bị thay đổi vọt, cần trigger báo lỗi thay vì âm thầm đưa qua MLP.
- Giám sát tỉ lệ tỷ lệ cắt tỉa (% synapses per pruning interval).

## 9. Architecture Update (ADR required)
Sắp tới cần tạo một **ADR (Architectural Decision Record)** trong thư mục `Documents/Architecture/02_ADR/` về việc quy chuẩn hóa kiến trúc cầu nối Encoder-Actor cho các Agent có module lai SNN-DNN, nhằm giải quyết triệt để sự xung khắc thời gian tính (Time-Scale Asymmetry).

## 10. Related
- `experiments.json` (multi_agent_complex_maze)
- `metrics.jsonl` log
