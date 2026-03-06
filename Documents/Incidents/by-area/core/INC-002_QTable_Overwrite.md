---
id: INC-002
title: Q-Table Memory Overwrite by Theus Context Engine
area: core
severity: critical
status: resolved
---

# Incident Report: INC-001 - Q-Table Memory Overwrite by Theus Context Engine

## 1. Summary
Trong môi trường `multi_agent_complex_maze`, agent gặp hiện tượng mất trí nhớ hoàn toàn ở thuật toán RL (Q-Learning). Bất chấp việc thực hiện hàng chục nghìn lượt chạy, kích thước Q-Table (`debug_q_table_size`) luôn bằng `0` hoặc `1`, dẫn đến agent mất khả năng đưa ra quyết định có ý nghĩa và liên tục đâm vào tường suốt 500 bước mỗi episode.

## 2. Background
Hệ thống EmotionAgent đang di chuyển từ Object-Oriented sang Process-Oriented Programming (POP) sử dụng Theus Engine. Dữ liệu trạng thái (State) được lưu trữ tại Context và được truyền qua các hàm thuần túy (Processes). Theus Engine quản lý việc đồng bộ (sync) Context thông qua việc nhận các `outputs` (dạng dictionary/delta) từ các process và ghi đè lại vào Global/Domain Context. Q-Table được thiết kế như một từ điển lớn lưu trữ tại `ctx.domain_ctx.heavy_q_table`.

## 3. What Went Wrong
Hàm `update_q_learning` trong `rl_processes.py` được thiết kế để tính toán TD-Error cho **một state duy nhất** (state gần nhất mà tác nhân trải qua). Process này tạo ra một dictionary tạm thời `delta_q_table` chỉ chứa một cặp key-value cho state vừa cập nhật, và trả dictionary này về engine dưới dạng:
```python
result_delta = {'heavy_q_table': delta_q_table}
```
Tuy nhiên, cơ chế kết hợp state của Theus Engine là **Shallow Overwrite** (ghi đè nông). Thuộc tính `heavy_q_table` của DomainContext bị thay thế hoàn toàn bởi `delta_q_table`. Kết quả: Toàn bộ tri thức tích lũy bị vứt bỏ, Q-Table quay về kích thước `1` sau mỗi bước học.

---

## 4. Comprehensive Analysis & Resolution Plan (Deep Incident Analysis Protocol)

### 4.1. Micro Analysis (Integrative Critical Analysis)
> **CORE INSIGHT:** Sự xung đột giữa kỳ vọng về Deep-Merge ngầm và hợp đồng (contract) cập nhật Shallow-Overwrite thực tế của hệ thống POP.

*   **The Trap (Sự nhầm lẫn logic):** Lập trình viên thiết kế process với giả định (false assumption) sai lầm rằng Theus Engine sẽ thực hiện "Deep Merge" cho các dictionary trả về (chỉ update key bị thay đổi).  
*   **The Truth (Sự thật hiện trường):** Theus tuân thủ POP nghiêm ngặt – dữ liệu trả về theo schema output sẽ trực tiếp thay thế object trong state hiện thời. Đây không phải là bug của Theus Engine, mà là sự nhầm lẫn về hợp đồng giao tiếp giữa Process và Context.

### 4.2. Macro Analysis (Systems Thinking Engine)
> 🌐 **SYSTEMS ANALYSIS**
> * **Scope:** Giao thức đồng bộ trạng thái giữa RL Process (Python) và State Manager (Rust Core của Theus).
> * **Dynamics:** Reinforcing Loop của RL (học tập làm thay đổi hành vi tương lai) bị phá vỡ hoàn toàn do Theus Engine thực hiện thao tác cân bằng huỷ diệt (Data Loss Delay) sau mỗi 1 timestep. Mạch phản hồi bị đứt đoạn gãy gọn.
> * **Root Structure:** Cấu trúc tĩnh trạng thái của POP yêu cầu mọi Process phải Pure và quản lý toàn vẹn dữ liệu. Cấu trúc Q-Table (một bảng băm nở rộng vô hạn) chống lại bản chất stateless nếu không được module hóa đúng phương pháp.
> * **Leverage Point:** Thay đổi luồng dữ liệu của cấu trúc khổng lồ (`heavy_q_table`) từ việc tạo delta keys sang thao tác đột biến in-place cẩn thận hoặc truyền tải dạng nguyên khối.

### 4.3. Ethical & Epistemic Audit 
*   **Humility (Sự khiêm tốn):** Chúng ta thường dễ dàng đổ lỗi cho thuật toán (RL không hội tụ, Hyperparameter sai). Sự thật là lỗi thuộc về hệ thống cơ sở hạ tầng (Context Pipeline).
*   **Courage (Sự can đảm):** Đối mặt với việc phải tìm ra cơ chế hỗ trợ đối tượng lớn (Heavy Objects) trong POP thay vì viết đường vòng tạm bợ. Việc chỉnh sửa Q-table nguyên khối hiện tại là giải pháp tạm, đòi hỏi kiến trúc bền vững hơn trong tương lai (ví dụ `ShmTensorStore`).

### 4.4. Solution Synthesis & Cascade Bug Fixes
1.  **Immediate Fix 1 (Q-Table In-place):** 
    Sửa đổi process `update_q_learning`. Lấy toàn bộ biến chiếu (reference) của `ctx.domain_ctx.heavy_q_table`, thực hiện cập nhật in-place, và trả về toàn bộ dictionary khổng lồ đó cho Theus ghi đè bằng chính nó.
2.  **Immediate Fix 2 (Context Merger Bypass):** 
    Phát hiện hàm `run_agent_step_pipeline()` trong `agent_step_pipeline.py` chạy các Process trực tiếp dưới dạng hàm Python thuần mà **không thông qua Theus Engine**. Hậu quả là mọi `delta` trả về (bao gồm cả Q-Table) đều bị vứt bỏ vào hư không. Giải pháp: Viết thêm hàm helper `_apply_delta()` để tự động catch và gộp các giá trị trả về vào lại `domain_ctx`.
3.  **Immediate Fix 3 (TypeError & NameError Fallouts):** 
    Việc kích hoạt lại luồng dữ liệu làm lộ ra các lỗi tiềm ẩn: Circuit breaker trong Coordinator trả về `float('-inf')` thay vì dict khiến `p_enrich_metrics.py` bị `TypeError`; và biến `prev_obs` bị sai chính tả thành `obs_prev` trong mô-đun Deep RL. Đã tiến hành vá toàn bộ.
4.  **Structural Fix (Cure):** 
    Đối với các dữ liệu phình to (như Q-Table), không nên lưu dưới dạng Python Dict trực tiếp chịu sự quản lý ghi đè của engine. Đề xuất: Đưa Q-Table lưu trữ dưới backend `ShmTensorStore`.

---

## 5. Impact
*   **Affected Entities:** Tất cả Agents học thông qua Q-learning và SNN.
*   **Severity:** Critical. Agent vĩnh viễn không thể học, gây lãng phí 100% tài nguyên tính toán.
*   **Significance:** Sự kiện này chứng minh rủi ro rất cao của việc rò rỉ bộ nhớ/dữ liệu bị đè kín giữa các Pipeline của kiến trúc POP khi developers lách luật (bypass engine state manager).

## 6. Resolution & Verification
*   **Fixed in Files:** `rl_processes.py`, `agent_step_pipeline.py`, `multi_agent_coordinator.py`, `run_experiments.py`.
*   **Verification:** Chạy lại file `run_experiments.py` thành công (nới lỏng Transaction Timeout lên 10 phút). File `metrics.jsonl` ghi nhận `debug_q_table_size` tăng liên tục (cán mốc > 200) thay vì kẹt ở 0; `avg_reward` và `avg_firing_rate` đã biến thiên linh hoạt.
*   **Status:** Resolved.

## 7. Preventive Actions & Architecture Update
*   Bổ sung Unit test kiểm định sự phát triển kích thước Q-Table.
*   ADR Đề xuất: Định nghĩa loại dữ liệu `TrackedList` thay vì List thông thường, hoặc chuyển dịch dữ liệu Q-table sang kiến trúc `ShmTensorStore` (Shared memory block) để thoát khỏi chu trình Read-Compute-Overwrite của Theus đối với object khổng lồ.
