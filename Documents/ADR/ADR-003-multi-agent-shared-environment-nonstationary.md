# ADR-003: Multi-Agent Scaling — Shared Environment Non-Stationarity

**Date**: 2026-05-15  
**Status**: Open  
**Context**: EmotionAgent — Multi-Agent Complex Maze (25×25 GridWorld, 5 switches, 4 dynamic gates)  
**Trigger**: Analysis of scaling `num_agents` from 1 → 5/10 in current architecture

---

## Vấn đề

Kiến trúc hiện tại cho phép nhiều agents chạy trong **cùng một GridWorld instance**. Điều này tạo ra 4 vấn đề cấu trúc độc lập với nhau:

### Vấn đề 1: Non-Stationarity trong Learning Signal

Mỗi agent học trong môi trường **thay đổi do chính các agent khác**:

```
Agent A bước → activate Switch B → Gate C mở
Agent B (cách Gate C 3 ô) nhận obs thay đổi đột ngột
Agent B nhận reward từ action của mình, nhưng state thay đổi do Agent A
→ Bellman gradient của Agent B bị contaminate
```

Cụ thể: với 5 switches, 4 gates — nếu 2 agents cùng activate switches trong 1 episode, agent thứ 3 **không cần học switch logic** vì gates đã mở sẵn. Policy học được không reproducible và không transferable sang single-agent inference.

Đây là vấn đề nền tảng của MARL (Multi-Agent Reinforcement Learning): trong shared environment với state dependencies, convergence của Independent Learners **không được đảm bảo về mặt lý thuyết** (Lowe et al. 2017, MADDPG paper).

### Vấn đề 2: Metrics Distortion

`success_rate` được tính là `sum(agent_success) / num_agents` per episode:

```python
# multi_agent_coordinator.py
success_rate = success_count / self.num_agents
```

Với 10 agents, 1 agent ngẫu nhiên tìm được goal → `success_rate = 0.10`. So sánh với `num_agents=1` là không valid. Toàn bộ historical data trong `compare_runs.py` bị invalidated nếu num_agents thay đổi giữa các run.

`avg_q_predicted` và `avg_firing_rate` hiện tại chỉ log **Agent 0**:

```python
# p_control_flow.py line 84
snn_global = runner.coordinator.agents[0].snn_ctx   # ← agents 1-9 vô hình
```

### Vấn đề 3: Python GIL Overhead trong ThreadPoolExecutor

```python
# multi_agent_coordinator.py
self._executor = ThreadPoolExecutor(max_workers=num_agents)
futures_step = [self._executor.submit(agent.step, env_adapter) for agent in self.agents]
```

SNN STDP, homeostasis PID, và Bellman backprop là **Python/CPU-bound code**. Python GIL prevent true parallelism cho CPU threads. Với 10 agents, overhead context switching có thể khiến wall-clock time > 10× single agent thay vì lý tưởng ~1× (CPU-bound parallelism không scale với threads trong Python).

Phase 2 (Sequential Acting) là **hard sequential** theo thiết kế:

```python
# multi_agent_coordinator.py — PHASE 2
for i, action in enumerate(actions):   # ← không thể parallel (GridWorld có collision dependency)
    reward = env.perform_action(i, ...)
```

**Ước tính thực tế**: 10 agents × 500 steps × phase overhead ≈ 40 phút/episode (vs 4 phút hiện tại).

### Vấn đề 4: Spawn Position Collision

```python
# environment.py line 21
default_starts = [[0, 0]] * self.num_agents
```

10 agents spawn tại `(0, 0)`. GridWorld không có agent-agent collision detection. Observations tại step 0 bị degenerate (cùng local view). Không crash, nhưng diversity của initial states — yếu tố quan trọng nhất của multi-agent diversity — bị triệt tiêu.

---

## Hệ Quả Bậc 2 (Second-Order Effects)

| Hệ quả | Mô tả | Severity |
|--------|-------|---------|
| Revolution Protocol misfire | `avg_reward` bị smooth-out → baseline tự-calibrate theo avg → Revolution không trigger hoặc trigger sai lúc | HIGH |
| Q-drift acceleration | Nhiều agents với bad local minima kéo `avg_q_predicted` xuống nhanh hơn, gradient của từng agent bị wrong direction | MEDIUM |
| OOM risk | 10 × 12.23MB tensors + 10 × 320 grad tensors + Python GC fragmentation trên RAM 8-16GB | MEDIUM |
| CLS invalidation | SNN của mỗi agent học trong environment context khác nhau → STDP synapse patterns của agent A không có ý nghĩa gì với agent B → Population-level STDP diversity không phải là "memory diversity", chỉ là "noise diversity" | HIGH |

---

## Options Đang Xem Xét

### Option A: Parallel Independent Environments (Recommended)

**Pattern**: Mỗi agent chạy trong **environment instance riêng biệt** (không share GridWorld state).

```python
# Thay vì 1 env cho N agents:
self.envs = [ComplexMazeEnvV2(self.config) for _ in range(num_agents)]

# Phase 2 có thể parallel hoàn toàn:
futures_act = [
    self._executor.submit(self._run_agent_step, i, actions[i])
    for i in range(self.num_agents)
]
```

- **Pro**: Loại bỏ non-stationarity hoàn toàn. Phase 2 trở thành embarrassingly parallel. Metrics valid.
- **Con**: RAM × N (có thể cần `multiprocessing` thay `threading` để bypass GIL nếu muốn true CPU parallelism).
- **Compatibility**: Không phá vỡ cấu trúc `coordinator.agents`. Chỉ thay đổi `run_episode()`.

### Option B: Cooperative Protocol với Explicit Communication

Giữ shared env nhưng thêm **communication channel** giữa agents (broadcast state delta per step). Mỗi agent nhận composite observation = local obs + social signal.

- **Pro**: Cho phép emergent cooperation (switch A → agent B learn gate C).
- **Con**: Phức tạp kiến trúc đáng kể. Non-stationarity không biến mất, chỉ được formally encode. Cần redesign GatedNet input dimension.

### Option C: Sequential Multi-Agent (No Parallelism)

Giữ nguyên shared env, chạy agents lần lượt (không concurrent), mỗi agent có episode riêng trong ngày. Effectively là N independent single-agent runs với shared initial SNN weights (sau Revolution).

- **Pro**: Không cần thay đổi architecture. Đơn giản nhất.
- **Con**: Không có intra-episode interaction. Revolution Protocol mất ý nghĩa "population" vì agents không cùng episode.

### Option D: Giữ nguyên num_agents=1, Tập trung CLS Quality

Thừa nhận rằng multi-agent diversity hiện tại không mang lại lợi ích rõ ràng ở giai đoạn này. Tiếp tục Run 2 với 1 agent. Sau khi có baseline chắc chắn (ε < 0.3, consistent success rate), mới xem xét lại multi-agent.

- **Pro**: Zero risk. Cho phép Run 2 hoàn thành cleanly.
- **Con**: Không khai thác Revolution Protocol. Population diversity = 0.

---

## Constraints & Requirements

1. **Metrics compatibility**: Nếu thay đổi `num_agents`, `compare_runs.py` phải được update để normalize per-agent (không per-episode).
2. **Checkpoint format**: `load_all_agents()` phụ thuộc vào số agents. Không thể resume checkpoint 1-agent sang 5-agent run.
3. **RAM budget**: Máy hiện tại ~400MB/agent. 5 agents = ~2GB — có thể chấp nhận. 10 agents = ~4GB — cần kiểm tra.
4. **`pid_ki` fix**: Bất kể option nào được chọn, fix này vẫn cần áp dụng cho run tiếp theo.

---

## Decision

**Chưa có quyết định. Status = Open.**

Cần thêm dữ liệu trước khi quyết định:
- [ ] Run 2 hoàn thành đến ε < 0.3 để có baseline 1-agent rõ ràng
- [ ] Benchmark RAM với 5 agents trên máy thực tế
- [ ] Verify `GridWorld` có thể được instantiated N lần không có side effects

**Hướng ưu tiên dự kiến**: Option A (parallel envs) nếu RAM cho phép, Option D nếu ưu tiên tiếp tục Run 2 không gián đoạn.

---

## Related

- [ADR-002](ADR-002-performance-bottleneck-16min-episode.md) — Performance bottleneck (wall-clock per episode)
- [INC-007](../Incidents/by-area/core/INC-007_Reward_Metric_Confounding_Exploration_Decay.md) — Reward metric confounding
- `src/coordination/multi_agent_coordinator.py` — Implementation
- `src/coordination/revolution_protocol.py` — Revolution Protocol Manager
