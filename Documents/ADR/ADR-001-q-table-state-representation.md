# ADR-001: Q-Table State Representation Thiếu Gate/Switch States

**Date**: 2026-03-11  
**Status**: Open  
**Context**: EmotionAgent — Multi-Agent Complex Maze  

---

## Vấn đề

Q-table hiện tại dùng state key chỉ encode **vị trí (x, y)** của agent:

```python
# rl_processes.py — observation_to_state_key()
pos = obs.get('agent_pos') or obs.get('position')
if pos:
    return f"{pos[0]},{pos[1]}"   # ← chỉ là "x,y"
```

Môi trường Complex Maze có **4 dynamic gates** (gate_A, gate_B, gate_C, gate_D) được điều khiển bởi **5 switches** (A, B, C, D, E). Trạng thái của gates thay đổi hoàn toàn ý nghĩa của bất kỳ vị trí nào trong maze.

---

## Hậu quả

Agent ở vị trí `(5, 5)` với `gate_A = CLOSED` và `gate_A = OPEN` sẽ **dùng cùng Q-values**:

```
Q("5,5") → action    ← mù trước gate states
```

- Agent không học được: "khi gate đóng, không đi hướng X; khi gate mở, đi hướng X"
- Policy sẽ không hội tụ dù học bao nhiêu episodes
- SNN emotion có thể bù đắp một phần qua curiosity-driven exploration, nhưng không đủ

---

## Bằng chứng

Sau episode đầu tiên thực sự chạy (2026-03-11):
- `q_table_size = 332` entries sau 500 steps × 5 agents trên grid 25×25 (625 cells)
- Agent 1 đến goal tại step 423 — **do may mắn ngẫu nhiên**, không phải do policy học được

---

## Giải pháp đề xuất

### Option A: Thêm switch states vào state key (đơn giản)

```python
def observation_to_state_key(obs):
    pos = obs.get('agent_pos', (0, 0))
    switches = obs.get('switch_states', {})
    # Encode: "x,y|A:0|B:1|C:0|D:0|E:0"
    switch_str = "|".join(f"{k}:{int(v)}" for k, v in sorted(switches.items()))
    return f"{pos[0]},{pos[1]}|{switch_str}"
```

**Trade-off**: State space tăng từ 625 lên 625 × 2^5 = 20,000. Q-table sẽ thưa hơn nhưng chính xác hơn.

### Option B: Dùng sensor_vector 16-dim làm state (phù hợp với SNN)

```python
def observation_to_state_key(obs):
    sensor = obs.get('sensor_vector')
    if sensor is not None:
        # Discretize và dùng làm key
        discretized = np.round(sensor[:4], 1)   # Chỉ lấy 4 channels quan trọng
        return str(discretized.tolist())
```

**Trade-off**: Bao gồm tất cả context agent cảm nhận được, nhưng discretization thô có thể gây collision.

### Option C: Bỏ tabular Q-learning, dùng Neural Q-Network với emotion gating (kiến trúc đúng)

`heavy_gated_network` đã tồn tại trong context nhưng chưa được khởi tạo và train đúng cách:

```python
# Trong select_action_gated():
if ctx.domain_ctx.heavy_gated_network is not None:
    # Neural Network Path ← đây mới là đường đúng
```

`GatedQNetwork(obs_dim=16, emotion_dim=16)` tự nhiên nhận toàn bộ sensor vector làm input — không cần discretization.

---

## Quyết định tạm thời

Chưa fix — cần thêm data từ nhiều episodes để xác nhận hypothesis. Ưu tiên Option A vì ít rủi ro nhất, sau đó chuyển dần sang Option C.

---

## Files liên quan

- [`rl_processes.py`](file:///c:/Users/dohoang/projects/EmotionAgent/src/processes/rl_processes.py) — `observation_to_state_key()` line 102
- [`environment.py`](file:///c:/Users/dohoang/projects/EmotionAgent/environment.py) — `get_observation()` line 185 (cần thêm `switch_states` vào observation)
- [`rl_agent.py`](file:///c:/Users/dohoang/projects/EmotionAgent/src/agents/rl_agent.py) — `observe_reward_and_learn()` line 314
