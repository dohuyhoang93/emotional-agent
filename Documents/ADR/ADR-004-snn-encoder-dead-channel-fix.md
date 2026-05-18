# ADR-004: SNN Encoder Dead Channel — 3-Component Fix

**Date**: 2026-05-18  
**Status**: Proposed  
**Context**: EmotionAgent — INC-008 (SNN Dead Channel), checkpoint_ep_1150 post-mortem  
**Trigger**: Probe xác nhận `snn_state_encoder` trả Q-values giống hệt nhau cho mọi SNN state (Q-std = 0.0000, cosine_sim = 1.000). Root cause chain được xác định đầy đủ qua 3 buổi phân tích.

---

## Bối Cảnh & Root Cause

### Root Cause Chain (INC-008)

```
Stage 1: W1 (1024×256) không train
  gradient(W1) = δ × x, x = firing_traces (mean=0.06) ≈ 0
  → Sau 1150 episodes: abs_max(W1) = 0.031250 = CHÍNH XÁC Kaiming init bound

Stage 2: Biases bị đẩy âm (trained, sai chiều)
  b1 gradient độc lập x → CÓ update
  LayerNorm khuếch đại gradient 23× khi h2 ≈ 0
  → b1 -= lr × positive_grad → 96.5% b1 âm

Stage 3: Runaway Loop (Reinforcing R1)
  b1 âm → 247/256 neurons chết → h2 ≈ ReLU(b2) = constant
  → LayerNorm(constant) = max amplification
  → b1 càng âm → lặp lại
  → Attractor ổn định: Q-head hấp thụ constant offset, ignore SNN
```

### Nguyên nhân gốc (Structural)

Kiến trúc giả định input distribution tương đồng cho cả 3 encoders (obs, emotion, snn). Thực tế `snn_state_encoder` nhận 1024-dim sparse binary input (mean=0.03–0.20) trong khi `obs_encoder` nhận 16-dim dense normalized vector (mean~0.5). Không có cơ chế nào xử lý sự bất cân xứng này.

### Khoảng trống thứ hai: Goal Signal

`get_sensor_vector()` (16-dim) không chứa thông tin về goal:
- **Channels 0-1**: Vị trí tuyệt đối (x/size, y/size)
- **Channels 2-9**: Tactile 8 hướng (wall=0.3, gate=0.6, switch=1.0, **goal=0.0 = trống**)
- **Channels 10-15**: Events, bumps, action strobe, time urgency

Goal cell không được detect từ ô kề. Tín hiệu goal duy nhất tới SNN là R-STDP dopamine tại thời điểm reward — retroactive, không predictive. Với success rate 5.3% (32/601 episodes), STDP nhận dopamine mạnh từ goal cực kỳ thưa thớt.

---

## Ba Quyết Định Kiến Trúc

---

### Decision 1: sqrt Input Normalization cho `snn_state_encoder`

**File**: `src/processes/snn_rl_bridge.py`  
**Thay đổi**: 1 dòng trong `_extract_snn_state_impl`

```python
# TRƯỚC (line 131):
current_state = torch.tensor(snn_state, dtype=torch.float32).detach()

# SAU:
current_state = torch.tensor(np.sqrt(snn_state + 1e-8), dtype=torch.float32).detach()
```

**Lý do chọn sqrt thay vì các alternatives:**

| Normalization | cos(dead,dying=3%) | cos(dead,healthy=20%) | Đặc điểm |
|---|---|---|---|
| Không norm | 0.9995 | 0.9270 | dying ≡ dead |
| **sqrt** | **0.9443** | **0.7885** | **cân bằng tốt nhất** |
| log1p×10 | 0.9810 | 0.7838 | yếu hơn với dying |
| L2-norm | 0.6544 | 0.6544 | mất thông tin cường độ |

**Tại sao sqrt tốt hơn L2-norm:** L2-norm chuẩn hóa tất cả non-zero inputs về cùng magnitude — dying (3%) và healthy (20%) trả về cosine giống hệt nhau với dead (0.6544 = 0.6544). Mất khả năng phân biệt "SNN đang chết dần" vs "SNN khỏe mạnh". sqrt bảo toàn cả pattern và intensity.

**Tính chất sqrt:**  
$$\sqrt{0.03} = 0.173 \quad (5.8\times \text{ amplification}), \quad \sqrt{0.50} = 0.707 \quad (1.41\times \text{ compression})$$

**Giới hạn của Decision này**: Khi firing_rate = 0 (tuyệt đối), sqrt(1e-8) ≈ 0 — encoder vẫn nhận near-zero. Tuy nhiên, homeostasis emergency rescue (line 103-108, `snn_homeostasis_theus.py`) đảm bảo rate không ở 0 lâu dài.

---

### Decision 2: Thay ReLU bằng tanh trong `snn_state_encoder`

**File**: `src/models/gated_integration.py`

```python
# TRƯỚC:
self.snn_state_encoder = nn.Sequential(
    nn.Linear(snn_state_dim, hidden_dim),
    nn.ReLU(),
    nn.Linear(hidden_dim, hidden_dim),
    nn.ReLU()
)

# SAU:
self.snn_state_encoder = nn.Sequential(
    nn.Linear(snn_state_dim, hidden_dim),
    nn.Tanh(),
    nn.Linear(hidden_dim, hidden_dim),
    nn.Tanh()
)
```

**Lý do:** ReLU tạo hard-zero cho pre-activation < 0 — với 96.5% biases âm, 247/256 neurons chết hoàn toàn. tanh không có dead zone:

$$\tanh'(x) = 1 - \tanh^2(x) > 0 \quad \forall x$$

**Bias gradient với tanh:**  
$$\frac{\partial L}{\partial b_1} = \delta \cdot \tanh'(W_1 x + b_1)$$

Nếu một số neurons có pre-activation dương và một số âm, gradient của $b_1$ có dấu mixed → không bị đẩy đồng loạt một chiều → loop R1 bị phá vỡ.

**Tại sao không dùng GELU:**  
- GELU: gradient norm = 2.61 (ổn định hơn), diversity = 0.8890  
- tanh: gradient norm = 10.65, diversity = 0.6899 (tốt hơn về diversity)  
- Chọn tanh vì diversity quan trọng hơn gradient stability ở giai đoạn này — encoder cần phân biệt các SNN states, không chỉ converge nhanh.

**Rủi ro saturation:** tanh bão hòa khi |pre| >> 1. Sau nhiều training episodes nếu weights lớn → gradients vanish. Cần monitor. Nếu xảy ra: thêm gradient clipping riêng cho snn_state_encoder (`max_norm=1.0`).

**Phạm vi áp dụng**: Cùng vấn đề tồn tại ở `emotion_encoder` (weight ratio = 1.000x, chưa train). Áp dụng Decision 2 cho cả hai encoders.

---

### Decision 3: Mở Rộng Sensor Vector 16 → 18 (Goal Direction Channels)

**File**: `environment.py`, method `get_sensor_vector()`

```python
# THÊM VÀO CUỐI get_sensor_vector(), thay thế channel 15 hiện tại
# (hoặc mở rộng vector từ shape 16 → 18):

# Kênh 15: Time urgency — GIỮ NGUYÊN (thông tin độc lập)
vector[15] = min(1.0, self.current_step / max(1, self.max_steps))

# Kênh 16: Goal direction — delta row (normalized)
goal_dr = (self.goal_pos[0] - pos[0]) / self.size
vector[16] = float(np.clip(goal_dr, -1.0, 1.0))

# Kênh 17: Goal direction — delta col (normalized)
goal_dc = (self.goal_pos[1] - pos[1]) / self.size
vector[17] = float(np.clip(goal_dc, -1.0, 1.0))
```

**Lý do:** Sensor hiện tại blind với goal (goal cell = 0.0 = trống). R-STDP nhận dopamine signal mạnh chỉ khi agent **đã đến** goal — retroactive, không predictive. Với success rate 5.3%, STDP không có đủ dữ liệu để hình thành goal-directed representations.

Thêm channels 16-17 cung cấp:
- **Gradient liên tục**: Mỗi step, agent biết "goal ở phía nào" → TD error có signal ngay cả khi chưa đến goal
- **STDP directional learning**: SNN có thể học "khi goal_dr âm (goal ở phía trên) + tôi đang ở vị trí X, tôi should fire neuron Y"
- **Ước tính tác động**: Từ `P(success|step) ≈ 1/maze_area` → `P(success|step) ∝ exp(-dist_to_goal)`

**Cascade dimension thay đổi:**

| Component | Trước | Sau | Ghi chú |
|---|---|---|---|
| `sensor_vector` shape | (16,) | (18,) | environment.py |
| `obs_encoder` | `Linear(16, 256)` | `Linear(18, 256)` | gated_integration.py |
| `emotion_encoder` | `Linear(16, 256)` | `Linear(16, 256)` | **KHÔNG ĐỔI** — emotion_vector từ SNN |
| `snn_state_encoder` | `Linear(1024, 256)` | `Linear(1024, 256)` | **KHÔNG ĐỔI** |
| `experiments.json` | `obs_dim: 16` | `obs_dim: 18` | config |
| STDP receptor loop | `i % 16` | `i % 18` | receptor mapping thay đổi |

**Cảnh báo quan trọng:** Decision 3 thay đổi philosophical premise của dự án. Sensor hiện tại theo thiết kế "agent blind to goal" (partial observability). Thêm goal direction chuyển từ sparse-reward exploration sang informed navigation. Đây là trade-off:
- **Blind to goal**: SNN phải phát triển goal-seeking behavior từ dopamine traces alone → scientifically purer nhưng cực kỳ khó học
- **Goal visible**: SNN có directional signal → STDP học nhanh hơn → nhưng contribution của SNN emotion khó đánh giá độc lập

---

## Hệ Quả Bậc 2 Toàn Cục

### Tương tác giữa 3 Decisions

```
Decision 3 alone:  SNN encodes goal patterns, BUT snn_state_encoder collapses → DQN 
                   improves chỉ từ obs_encoder (goal_dr, goal_dc trực tiếp)
                   
Decision 1+2 only: Encoder reads SNN faithfully, BUT SNN patterns không có goal content
                   → marginal improvement only

Decision 1+2+3:    SNN encodes goal proximity (Decision 3)
                   Encoder reads it faithfully (Decision 1+2)
                   → Positive R1 loop: goal_signal → STDP → h_snn → better policy
                   → Reinforcing loop có thể stabilize hoặc oscillate
```

### Rủi ro Co-Evolution Non-Stationarity

Khi cả 3 decisions active, DQN policy thay đổi → trajectories khác → SNN input distribution khác → STDP patterns khác → h_snn khác → policy thay đổi tiếp. Đây là moving target problem:

**Giảm thiểu:** STDP learning rate (`dopamine_learning_rate`) nên nhỏ hơn DQN learning rate để SNN stabilize trước khi DQN thích nghi. Tỷ lệ khuyến nghị: `lr_stdp / lr_dqn < 0.1`.

### SNN Contribution Risk (Filter B)

Decision 3 tạo rủi ro: nếu DQN cải thiện mạnh sau fix, không rõ nguyên nhân là obs_encoder đọc goal_dr/goal_dc trực tiếp hay snn_state_encoder đọc SNN patterns. Cần ablation study:

```
Run A: All 3 decisions (full fix)
Run B: Decision 3 only, snn_state_encoder frozen as zeros (obs_encoder baseline)
Run C: Decision 1+2 only, no goal signal (encoder fix baseline)

Nếu perf(A) ≈ perf(B) → SNN contribution = 0 (encoder fix vô nghĩa)
Nếu perf(A) > perf(B) > perf(C) → SNN đóng góp có ý nghĩa
```

---

## Constraints Không Thay Đổi

1. **STDP/backprop boundary giữ nguyên**: `firing_traces.copy()` → `.detach()` wall ở `snn_rl_bridge.py:131`. Gradient không bao giờ flow ngược vào SNN.
2. **Homeostasis stack giữ nguyên**: 5 tầng bảo vệ (regular, emergency rescue, PID meta, dream penalty, threshold floor) không thay đổi.
3. **AttentionBlock giữ nguyên**: Sigmoid gate (không phải Softmax) vì seq_len=1. Không cần thay đổi.
4. **Bắt buộc train từ ep_0**: checkpoint_ep_1150 không thể resume. Q-head đã hấp thụ constant h_snn offset. Decision 3 còn làm invalidate architecture (obs_dim 16→18).

---

## Quyết Định Phân Kỳ (Decisions NOT taken)

| Alternative | Lý do từ chối |
|---|---|
| L2-norm thay sqrt | Mất thông tin cường độ — dying (3%) ≡ healthy (20%) sau L2, DQN không phân biệt được "SNN đang suy yếu" |
| GELU thay tanh | GELU có gradient ổn định hơn (norm=2.61 vs 10.65) nhưng diversity kém hơn (0.889 vs 0.690). Ở giai đoạn fix, diversity ưu tiên |
| global_rate scalar riêng | Homeostasis đảm bảo firing_rate > 1e-6 (emergency rescue). Scalar riêng là redundant trong steady state |
| Manhattan distance thay goal_dr/goal_dc | Manhattan scalar mất thông tin direction (trái/phải/trên/dưới). Agent cần biết hướng, không chỉ khoảng cách |
| Giữ nguyên 16-dim, thêm reward shaping | Reward shaping thay đổi DQN learning signal nhưng không cho SNN spatial goal context |

---

## Implementation Order

1. **Decision 1** (`snn_rl_bridge.py`) — 1 dòng, không cần restart architecture  
2. **Decision 2** (`gated_integration.py`) — 4 dòng, invalidate all checkpoints  
3. **Decision 3** (`environment.py` + `gated_integration.py` + `experiments.json`) — cascade, thực hiện cuối cùng  
4. **Verification**: Probe encoder diversity sau fresh init với new architecture  
5. **Ablation**: Chạy Run A/B/C (xem section rủi ro) để xác nhận SNN contribution  

---

## Status & Open Questions

| Câu hỏi | Trạng thái |
|---|---|
| Decision 3 có phá vỡ philosophical premise "blind agent"? | **Open** — cần team alignment |
| tanh vs GELU final choice | **Open** — cần experiment |
| Ablation run được ưu tiên hay full fix trước? | **Open** |
| `emotion_encoder` cũng áp dụng Decision 2? | **Decided: Yes** (same weight ratio = 1.000x) |
| STDP `dopamine_learning_rate` cần tune lại? | **Likely Yes** — với goal signal, dopamine dày đặc hơn |
