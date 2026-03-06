---
id: INC-003
title: Static Sensor Input causing Cognitive Freeze in SNN
area: core
severity: high
status: resolved
---

# Incident Report: INC-003 - Static Sensor Input causing Cognitive Freeze

## 1. Summary
Trong quá trình huấn luyện Reinforcement Learning (RL) tích hợp Spiking Neural Network (SNN), khi Agent bị mắc kẹt (đâm vào tường, vật cản cứng) liên tục, đầu vào cảm biến `sensor_vector` từ môi trường `GridWorld` bị tĩnh hoàn toàn. Việc thiếu vắng sự biến thiên trong dữ liệu đầu vào khiến mạng nơ-ron SNN rơi vào trạng thái "đóng băng nhận thức" (Cognitive Freeze), điện thế nơ-ron giảm phân rã đều và độ ngạc nhiên (Novelty) tiệm cận 0, làm đứt gãy hoàn toàn vòng lặp học hỏi hệ thống.

## 2. Background
Hệ thống sử dụng cơ chế STDP 3 yếu tố (3-factor STDP) cho SNN, đòi hỏi phải có sự chênh lệch thông tin (Spike Timing) liên tục để tạo ra phần thưởng nội tại (Intrinsic Reward) - sự tò mò. Môi trường `GridWorld` hiện tại truyền mảng 16-chiều chứa thông tin vị trí các vật thể xung quanh.

## 3. What Went Wrong
Hàm `get_sensor_vector` trong môi trường chỉ ánh xạ không gian tĩnh (phong cảnh). Khi Agent quyết định thực hiện một hành động di chuyển (Move D/U/L/R) nhưng bị chặn lại bởi bức tường, vị trí không đổi, suy ra khung cảnh cảm biến không đổi: $I_t = I_{t+1}$.
- Đối với RL thông thường: Có Reward âm (-10) để trừng phạt lỗi vật lý.
- Đối với SNN: Không có Reward âm, không có thông tin va chạm thô. SNN nghĩ rằng Agent đang "đứng yên chiêm ngưỡng" một cảnh vật an toàn, dẫn đến buồn ngủ (giảm Spike rate) thay vì hoảng sợ (tăng Spike rate) như đúng lý luận sinh học.

Đây là lỗ hổng trong **Kiến trúc Nhận thức (Cognitive Architecture)**, cụ thể là chứng "Mù Xúc Giác" (Haptic Blindness), gây nhiễu loạn luồng dữ liệu học tập liên hợp STDP-RL.

### Phát hiện mới: Lỗi Double Move (Di chuyển kép)
Trong quá trình gỡ lỗi chuyên sâu, chúng tôi phát hiện một lỗi kiến trúc nghiêm trọng làm trầm trọng hóa vấn đề:
- **Cơ chế lỗi:** Agent đang tự thực hiện hành động (`perform_action`) bên trong pipeline của nó, sau đó `Coordinator` lại gọi thực hiện hành động đó một lần nữa.
- **Hệ quả:** Agent di chuyển 2 ô mỗi bước, làm trôi vị trí và xóa sạch trạng thái va chạm `last_bump_types` ngay lập tức trước khi bước Perception tiếp theo kịp đọc dữ liệu. Điều này giải thích tại sao cảm biến luôn trả về 0 kể cả khi có va chạm thực tế.

> [!NOTE]
> **Góc nhìn Khách quan (Intellectual Empathy):** Cần thừa nhận rằng thiết kế vision-only hiện tại vốn được tối ưu hóa cho tài nguyên tính toán và là tiêu chuẩn mặc định cho phần lớn các bài toán GridWorld đơn giản. Lỗi chỉ phát sinh khi hệ thống được đẩy vào môi trường Mê cung phức tạp với mật độ va chạm cao, nơi mà sự khác biệt giữa "đứng yên" và "bị chặn" trở nên sống còn đối với mạng nơ-ron spiking.

---

## 4. Comprehensive Analysis & Resolution Plan (Systems Thinking Engine Protocol)

> 🌐 **SYSTEMS ANALYSIS**
> * **Scope:** Giao thức đồng bộ trạng thái giữa **Container** (Môi trường Gridworld Simulation) và **Actors** (SNN Receptor Layer, RL Policy Module). Giới hạn ở luồng dữ liệu một chiều từ Environment Output sang Agent Input.
> * **Dynamics:** Hệ thống chứa một Vòng lặp Cân bằng (Balancing Loop B1 - RL Punishment) vành ngoài bị đứt gãy mạch nối với Vòng lặp Gia cố (Reinforcing Loop R1 - SNN Emotion Generation) vành trong. Có độ trễ (Delay) zero giữa Action và Sensor, nhưng lại có độ trễ vĩnh viễn (Infinite Delay) giữa Action và SNN Novelty do nhiễu vật lý bị triệt tiêu ở Cảm biến Không gian.
> * **Root Structure:** Quyết định kiến trúc sai lầm: Đồng nhất hóa "Observation Không gian tĩnh" với "Sensor Input" của một tác nhân sinh học.
> * **Leverage Point:** Thêm chiều **Proprioceptive Feedback (Phản hồi Xúc giác)** vào Sensor Input để tái thiết lập dây chằng giao tiếp giữa Balancing Loop của môi trường và Reinforcing Loop của não bộ tác nhân.

### Phase 1: Boundary Mapping (The Scope)
*   **Container:** `GridWorld` - Môi trường Lưới 2D xử lý vật lý và hình ảnh.
*   **Actors:** 
    *   `EnvironmentAdapter`: Cầu nối chuyển đổi dữ liệu.
    *   `SNN_Core`: Quản lý các gai (Spike) định hướng sự kiện.
    *   `RL_Agent`: Cập nhật trọng số thông qua Error.
*   **The Flaw in Scope:** `GridWorld` được xem là "bên ngoài" (Outside), nhưng cảm giác "đau đớn/va chạm" lẽ ra phải nằm ở "Ranh giới" (Boundary / Da) của Agent. Việc môi trường không mô phỏng Cảm giác Bản thể (Proprioceptive) đã để lọt khe sự kiện chạm viền.

### Phase 2: Dynamic Analysis (The Links & Loops)
*   **Balancing Loop (B1) - The RL Logic:** Agent đâm tường -> Reward = -10 -> Q-value suy giảm. Vòng lặp này hoạt động đúng, nhưng nó chỉ là phản xạ có điều kiện muộn màng.
*   **Reinforcing Loop (R1) - The SNN Emotion:** Sensor Input -> Spike Generation -> Hạch Hạnh Nhân cập nhật Cảm xúc -> Kích thích RL. Vòng lặp này bị **đóng băng**.
*   **The Disconnect:** Hành động vật lý sinh ra Lực cản (Force), nhưng `Observation` lưới lại tịnh tiến (Translation). Sensor tĩnh = 0 Spike. Lỗi không nằm ở RL hay SNN, mà ở dây truyền dẫn bị thiếu (The Missing Link).

### Phase 3: Structural Excavation (The Root)
*   **The Event:** Agent đâm đầu vào tường liên tục đến hết 500 bước với Q-value = 0.
*   **The Pattern:** Xảy ra ở tất cả các Agent hễ đi lọt vào góc chết (Corner Trap).
*   **The Structure (Mental Model Error):** Người thiết kế hàm `get_sensor_vector` chỉ lập trình hệ thống Thị Giác (Vision), trong khi quy trình STDP 3 yếu tố yêu cầu độ sốc về thời gian/di chuyển. Việc thiếu vắng Xúc Giác (Haptic/Pain) làm triệt tiêu bản chất Sinh học của mạng.

### Phase 4: Leverage & Simulation (The Solution)
**Pivot Point: The Extended Proprioceptive & Arousal Protocol**
Tận dụng toàn bộ các kênh dự phòng (12-15) để xây dựng hệ thống cảm giác toàn diện:
1.  **Kênh 12 (Static_Bump):** Bật `1.0` khi đâm tường tĩnh. Giúp SNN phân biệt vật cản bất biến.
2.  **Kênh 13 (Dynamic_Bump):** Bật `1.0` khi đâm cửa đóng/vật thể động. Giúp nảy sinh kỳ vọng về việc trạng thái này có thể thay đổi trong tương lai (kích thích tò mò).
3.  **Kênh 14 (Action_Strobe):** Bật `1.0` mỗi khi Agent hành động. Duy trì nhịp sinh học cho nơ-ron spiking.
4.  **Kênh 15 (Internal_Pressure):** Tín hiệu Ramping ($current\_step / max\_steps$). Tăng dần độ "hoảng loạn" (Arousal) khi thời gian cạn kiệt, buộc nơ-ron thay đổi ngưỡng phát hỏa (firing threshold).

*2nd-Order Effect Check (Kiểm tra Phản ứng phụ):* Việc gán các giá trị này vào kênh 12-15 hoàn toàn tách biệt với dữ liệu thị giác (nguyên tử hóa đầu vào), đảm bảo không gây nhiễu loạn cho các liên kết đã học mà chỉ bổ sung thêm các "chiều kích" cảm xúc mới.

> [!IMPORTANT]
> **Giới hạn Giải pháp (Intellectual Humility):** Mặc dù giải pháp 4 kênh giải quyết triệt để vấn đề "đóng băng nhận thức", hiệu quả hội tụ cuối cùng vẫn phụ thuộc chặt chẽ vào cấu trúc trọng số của Gated Network. Đây là nền tảng cảm giác (Sensation) cần thiết để xây dựng Nhận thức (Cognition).

---

## 5. Impact
*   **Affected Entities:** Spiking Neural Network, Intrinsic Reward Module.
*   **Severity:** High -> Critical. Agent rơi vào vòng lặp hành vi tự hoại (Learned Helplessness) nếu vô tình kẹt vào các hẻm hẹp trên map. Sự kiện có thể làm sụp đổ toàn bộ giá trị trải nghiệm tại thời điểm đó.
*   **Significance:** Lỗi chứng minh RL phạt bên ngoài là chưa đủ cho mạng định hướng SNN, SNN cần đầu vào nhạy cảm với các pha biến dạng vật lý nội bộ.

## 6. Resolution & Fixed In
*   **Target Files to fix:** `environment.py`, `agent_step_pipeline.py`, `rl_agent.py`, `multi_agent_coordinator.py`.
*   **Status:** Resolved.
*   **Giải pháp Kiến trúc:** Tước quyền thực thi của Agent. Giờ đây Agent chỉ làm nhiệm vụ Nhận thức -> Suy nghĩ. Việc Thực thi và Phản hồi học tập được dồn về `MultiAgentCoordinator` quản lý tập trung để đảm bảo tính nhất quán 1-ô-mỗi-bước và bảo toàn tín hiệu va chạm.

## 7. Preventive Actions 
*   Bổ sung Unit test cho Môi trường: Mô phỏng hành động "Move" vào ô tường, yêu cầu assert các bit kênh 12-15 của `sensor_vector` bị thay đổi lớn.
