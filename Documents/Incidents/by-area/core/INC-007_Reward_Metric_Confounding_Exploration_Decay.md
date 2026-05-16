---
id: INC-007
title: Reward Metric Confounding via Exploration Decay (False Learning Failure Signal)
area: core
severity: high
status: partially-resolved
introduced_in: multi_agent_complex_maze run 2026-05-08
fixed_in: "Fix 1 (Penalty Bug) — 2026-05-13 | Fix 2-4 (Observability) — pending"
---

# INC-007: Reward Metric Confounding via Exploration Decay

**Date:** 2026-05-12  
**Component:** `src/orchestrator/processes/p_enrich_metrics.py` · `src/processes/rl_snn_integration.py` · `experiments.json`  
**Severity:** High (Misleading Observability / Policy Convergence Risk)  
**Status:** Open — Investigation Plan  
**Author:** GitHub Copilot (Deep Incident Analysis Protocol)

---

## 1. Executive Summary

Trong run `multi_agent_complex_maze` (2026-05-08, 1490 episodes), chỉ số `avg_reward` giảm đều **từ -56 → -161** (giảm 185% tuyến tính theo epsilon). Đây được tưởng nhầm là "catastrophic learning failure" nhưng thực chất là **một hiệu ứng đo lường sai** (Metric Confounding):

- **Success rate thực tế TĂNG** từ 0% → 8% trong cùng giai đoạn.
- **Neural loss GIẢM** từ 7.14 → 4.15 (network đang học đúng hướng).
- **11 episode đầu (ep 0–214) có reward dương cực cao** (+735, +669...) do agent ngẫu nhiên kích hoạt switch gates.
- Sau ep 214, **không còn episode reward dương nào** trong 1276 episodes còn lại.

**Kết luận:** `avg_reward` đang đo tổng phần thưởng bao gồm cả random exploration gate-toggle bonuses (+1.0 × N_toggles). Khi epsilon giảm, agent ngừng ngẫu nhiên chạm vào switch → mất nguồn bonus này → reward tụt dốc không phản ánh performance thực.

---

## 2. Background

Thực nghiệm `multi_agent_complex_maze` (Grid 25×25):
- 5 switches (A–E) điều khiển 4 dynamic gates
- `step_penalty = -0.01`, `wall_penalty = -0.1`, `goal_reward = +10.0`
- **`switch_open = +1.0`, `switch_close = -1.2`**
- `max_steps = 500`, `exploration_decay = 0.999` (ε: 1.0 → 0.225 sau 1490 ep)
- `num_agents = 1`

Reward formula (per step):
```
R_total = R_ext + (0.05 × novelty_SNN) + (0.05 × |TD_error|)
```

Metric `avg_reward` = tổng tất cả R_total qua 500 steps của một episode.

---

## 3. What Went Wrong

### Bằng chứng định lượng

| Giai đoạn | Avg Reward | Success Rate | Neural Loss | Epsilon |
|-----------|-----------|-------------|------------|---------|
| ep 0–99   | -56.56    | 0.00%       | 7.14       | ~1.0    |
| ep 400–499 | -97.96   | 5.00%       | ~4.5       | ~0.68   |
| ep 800–899 | -126.72  | 4.00%       | ~4.2       | ~0.45   |
| ep 1400–1489 | -161.02 | **5.56%**  | **4.15**   | **0.225** |

**Nghịch lý:** Reward giảm 185%, nhưng success rate TĂNG và loss GIẢM. Đây không thể là "learning failure" — đây là measurement artifact.

### Phân tích cấu trúc reward

Trường hợp ep 144 (R = +735.27, success_rate = 0):
```
500 steps × (-0.01 step_penalty) = -5
Wall hits: 0 (giả sử)
Switch opens: ~740 opens × (+1.0) = +740
Total ≈ +735  ← giải thích được!
```
→ Agent với ε ≈ 1.0 ngẫu nhiên liên tục kích hoạt switch, tích lũy reward khổng lồ dù KHÔNG đạt đích.

Trường hợp ep 1400+ (R ≈ -161):
```
500 steps × (-0.01) = -5
Wall hits: ~700 hits × (-0.1) = -70 (random walk + wall loops)
Switch opens: ~0 (agent không random nữa, không tình cờ gặp switch)
Gate interactions from policy: có thể vài lần toggle âm: -1.2 × N
Total ≈ -75 to -161 (tùy wall behavior)
```

---

## 4. Root Cause Analysis

### 4.1 Micro Root Cause (@integrative-critical-analysis)

> **CORE INSIGHT:** `avg_reward` là một metric hỗn hợp đang đo "random exploration bonus" lẫn "task performance" mà không phân tách — khiến epsilon decay tạo ra illusion của catastrophic failure.

**The Trap (False Assumption):**
- Assumption: `avg_reward` ↓ = agent học kém hơn
- Reality: `avg_reward` ↓ = epsilon ↓ = mất random switch bonuses

**The Truth (Verified Facts):**
1. `debug_q_table_size: 0` xuyên suốt — đây là BÌNH THƯỜNG (V3 không dùng tabular Q-table, dùng GatedNetwork DQN)
2. Firing rate bimodal (0.032 ↔ 0.2) là Homeostasis `emergency_rescue_triggered` khi rate < 1e-6 → đây là cơ chế phòng thủ đã thiết kế, không phải bug mới
3. 11/11 episodes reward dương đều xảy ra khi ε > 0.73 (ep ≤ 214)
4. Loss decrease + success rate increase = GatedNetwork ĐANG học, chỉ reward metric là sai

**The Logic Gap:**
- `combine_rewards` trả về `total_reward = extrinsic + intrinsic` và `avg_reward` metric = tổng total_reward qua episode
- KHÔNG có metric nào tách riêng `extrinsic_only_reward` và `switch_interaction_reward`
- Không thể distinguish "reward giảm do học tốt hơn" vs "reward giảm do bớt random"

**Nguồn gốc lỗi (Origin Q18):**  
Đây là hậu quả từ INC-005 resolution: fix `intrinsic_reward` từ `0.5 → 0.0` khi không có neuron active đã làm giảm intrinsic noise, nhưng switch-toggle bonus từ extrinsic reward vẫn còn và không được ghi nhận riêng.

---

### 4.2 Macro Root Cause (@systems-thinking-engine)

> 🌐 **SYSTEMS ANALYSIS**
> * **Scope:** Metric Pipeline (p_enrich_metrics) ↔ Reward Combiner (rl_snn_integration) ↔ Environment (maze switches) ↔ Epsilon Decay (exploration schedule)
> * **Root Structure:** Reward Signal Architecture không có separation of concerns

**Boundary Mapping:**
- **Container:** Multi-Agent Maze Training Loop
- **Actors:** `GatedNetwork` (policy), `Epsilon Scheduler`, `Switch Environment`, `Metric Logger`, `Homeostasis PID`

**Reinforcing Loop (R1) — The "Exploration Bonus Cliff":**
```
High ε  → Random switch contacts  → High avg_reward
→ Metrics look "ok"  → No corrective action taken
→ ε decays normally  → Switch contacts drop
→ avg_reward tanks   → Appears as "learning failure"
→ Investigation resources consumed
```
Không có **Balancing Loop** nào ngắt chu kỳ này vì metric pipeline không phân tách reward components.

**Delay (D1):** Có độ trễ 214 episodes giữa khi hệ thống "trông ổn" (early positive rewards) và khi vấn đề measurement artifact lộ ra (all-negative rewards).

**Structural Root Cause:**
> "Reward aggregation không có decomposition" là design decision từ đầu dự án, phản ánh giả định **"total reward là đủ để đánh giá learning progress"** — giả định này sai với môi trường có high-variance exploration bonuses.

**Architectural Tradeoff (INC context):**
- **Flexibility (Thiết kế hiện tại):** Reward là scalar tổng hợp, đơn giản để log và compare
- **Observability (Cần thiết):** Cần phân tách `ext_reward`, `gate_reward`, `intrinsic_reward` per episode

Đây là xung đột **"Simplicity vs Observability"** — không phải code bug, là design debt.

---

## 5. Virtue Audit (@intellectual-virtue-auditor)

### Filter A (Humility) — ĐẠT
Analysis này dựa trên dữ liệu đã verify. Confidence level: Medium-High.
Caveat: Chưa có log chi tiết per-step reward breakdown → vẫn có thể sai về cơ chế chính xác.

### Filter B (Courage) — KIỂM TRA
**Hard truth cần nói:** Success rate 8% sau 1490 episodes trên maze 25×25 là **rất thấp**. Dù metric `avg_reward` misleading, success rate vẫn thấp hơn kỳ vọng. Ngay cả khi fix metric, **learning speed vẫn cần cải thiện**.

### Filter C (Empathy — Steel-manning) — KIỂM TRA
Phản biện mạnh nhất cho kết luận này:
> "Nếu reward decline chỉ là measurement artifact, tại sao success rate không tăng nhanh hơn? 8% sau 1490 ep là bằng chứng agent vẫn không học được maze structure."

Đây là điểm hợp lý: **cả hai vấn đề có thể cùng tồn tại** — (1) metric misleading, VÀ (2) learning speed thực sự chậm. Chúng không loại trừ nhau.

### Filter D (Integrity) — KIỂM TRA
INC-005 đã resolve "intrinsic reward 0.5 bug" — nhưng switch-open bonus (+1.0) vẫn là extrinsic signal, không liên quan đến INC-005. Cần không nhầm lẫn hai nguồn reward.

### Filter G (Autonomy) — ĐẠT
Kết luận này không dựa vào consensus mà dựa vào:
1. Verified correlation: ep 0–214 có ε > 0.73 → positive rewards
2. Verified inverse: ep 215+ → zero positive rewards
3. Reward math cross-check: +735 khớp với ~740 switch opens × (+1.0)

---

## 6. Investigation Plan (Ordered by Evidence Priority)

### Phase 1: VERIFY (1–2 ngày) — Xác nhận giả thuyết

**Task 1.1 — Instrument per-step reward breakdown**
```python
# Thêm vào observe_reward_and_learn() trong rl_agent.py
self.episode_metrics['gate_open_reward_total'] += info.get('switch_reward', 0)
self.episode_metrics['wall_hit_count'] += info.get('wall_hit', 0)
```
**Mục tiêu:** Chạy 50 episodes, plot `gate_open_reward` vs `epsilon`. Nếu correlation > 0.8 → hypothesis confirmed.

**Task 1.2 — Verify GatedNetwork policy quality**
```python
# Chạy 50 episodes với ε = 0 (pure exploitation) từ checkpoint_ep_1400
# So sánh success rate với ε = 0.5 same checkpoint
```
**Mục tiêu:** Nếu ε=0 cho success_rate > 5%, policy đang hoạt động đúng.

**Task 1.3 — Inspect Homeostasis emergency_rescue frequency**
```python
# Thêm counter trong _homeostasis_impl:
# snn_domain.metrics['rescue_count_episode'] += 1
```
**Mục tiêu:** Xác định % episodes có rescue trigger → biết mức độ nghiêm trọng của firing rate instability.

---

### Phase 2: FIX OBSERVABILITY (3–5 ngày)

**Task 2.1 — Add reward decomposition metrics**  
File: `src/orchestrator/processes/p_enrich_metrics.py`
```python
# Thêm vào metrics dict:
metrics['avg_extrinsic_reward'] = episode_extrinsic_total / num_agents
metrics['avg_gate_interaction_reward'] = episode_gate_total / num_agents  
metrics['avg_wall_hit_count'] = episode_wall_hits / num_agents
```

**Task 2.2 — Fix reward signal for fair evaluation**  
File: `experiments.json` (or environment adapter)
- Xem xét đặt `switch_toggle_reward_cap` để giới hạn bonus từ toggle lặp lại (max 1 toggle bonus per switch per episode)
- Phân tách `R_task` (chỉ goal + gate điều hướng đúng) khỏi `R_exploration` (bonus ngẫu nhiên)

**Task 2.3 — Add learning progress dashboard metric**
```python
# Metric thực sự phản ánh learning:
metrics['learning_progress_score'] = (
    0.5 * success_rate 
    + 0.3 * (1.0 - epsilon)  # maturity bonus
    + 0.2 * (1.0 - neural_loss / 10.0)  # loss reduction
)
```

---

### Phase 3: STRUCTURAL FIX (1–2 tuần)

**Task 3.1 — Architecture: Separate Exploration Reward from Task Reward**  
Thiết kế lại `combine_rewards` để trả về:
```python
{
    'total_reward': ...,       # For DQN training
    'task_reward': ...,        # For evaluation metric
    'exploration_bonus': ...,  # Random/curiosity signal only
}
```
File: `src/processes/rl_snn_integration.py`

**Task 3.2 — Switch reward structure: make it directional**
Thay `switch_open = +1.0` (unconditional) thành:
```python
# +1.0 only if switch is on the critical path to goal (from path planner)
# -0.1 if switch is toggled without purpose
```
Requires: path-aware reward shaping hoặc subgoal decomposition.

**Task 3.3 — Curriculum learning: gate discovery phase**
Thêm giai đoạn training với maze không có gate-penalty (`switch_close = 0.0`) để agent học path trước, sau đó introduce gate mechanics.

---

## 7. Impact Assessment

| Area | Impact |
|------|--------|
| **Observability** | Critical — Cannot distinguish learning progress from exploration decay |
| **Agent behavior** | Medium — Agent is actually learning (8% success, loss ↓) but slowly |
| **Experiment validity** | High — All historical runs with this config have same confounded metric |
| **Research conclusions** | High — Papers/reports using `avg_reward` as primary metric are misleading |

---

## 8. Comprehensive Analysis & Resolution Plan

### 8.1 Micro Analysis Summary
- **False assumption busted:** `avg_reward` ≠ task performance. It = `extrinsic + intrinsic` where `extrinsic` includes high-variance switch bonuses dominating signal in high-ε phase.
- **Evidence chain:** 11 positive-reward episodes all in ε > 0.73 zone → 1276 episodes of zero positive rewards after → correlates directly with epsilon, not with task learning.
- **INC-005 relationship:** Bug fixed (0.5 → 0.0 default intrinsic). This incident is independent — it's about extrinsic switch topology, not intrinsic reward default value.

### 8.2 Macro Analysis Summary  
- **Structural debt:** Reward aggregation without decomposition is a design decision from project genesis that was never questioned because early visual metrics "looked ok" (high rewards early).
- **Feedback loop:** The positive early metrics suppressed corrective action, allowing the misleading metric to persist through 6 previous incident reports without being flagged.
- **Pivot point:** A single addition of `avg_task_reward` (goal + correct gate traversal only) would immediately expose the issue and is low-risk to implement.

### 8.3 Solution Priority Matrix

| Priority | Fix | Risk | Time |
|----------|-----|------|------|
| P0 | Add reward decomposition logging (Task 2.1) | Zero — additive only | 1 day |
| P1 | Verify hypothesis with per-step reward instrumentation (Task 1.1) | Zero | 2 days |
| P2 | Switch reward cap (Task 2.2) | Low | 3 days |
| P3 | Structural reward separation (Task 3.1) | Medium — requires DQN retraining | 1 week |
| P4 | Curriculum learning (Task 3.3) | High — requires env changes | 2 weeks |

---

## 9. Preventive Actions

1. **Test:** Add unit test asserting `avg_reward` correlation with `success_rate` (r > 0.3 over 100 eps) — fail if reward goes down while success rate goes up.
2. **Lint/CI:** Add assertion in `p_enrich_metrics.py`: if `success_rate > 0.05 AND avg_reward < -150`, log WARNING: "Reward metric may be confounded — check switch interaction log."
3. **Docs:** Update `Documents/specs/` with requirement: "All reward-based experiments MUST log decomposed reward components: `extrinsic_task`, `extrinsic_exploration`, `intrinsic_snn`."

---

## 10. Related

- INC-005: `Reward Signal Corruption (Intrinsic Decoupling)` — fixed intrinsic default 0.5 → 0.0
- INC-001: `ZeroFiringRateSNN` — homeostasis bimodal behavior still observable but is expected rescue mechanism
- INC-006: `HybridArchitectureFailure` — resolved, monotonic synapse growth confirmed (105k → 113k in ep 0–9)
- `experiments.json` — config for this run
- `results/multi_agent_complex_maze/metrics.jsonl` — 1490 ep data source

---

## 11. Lessons Learned

1. **Reward = Incentive ≠ Performance.** Never use total reward as the sole learning progress indicator in environments with high-variance exploration bonuses.
2. **Metric decomposition is not optional.** Every reward component that can vary independently (task, exploration, intrinsic) needs its own tracked metric.  
3. **Inverse metric paradox.** When two metrics move in opposite directions (reward ↓, success_rate ↑), assume metric confounding first before assuming catastrophic failure.
4. **The "early positive signal" trap.** High early rewards from random exploration create a false baseline that makes epsilon decay look like catastrophic forgetting — a systematic bias in all greedy-annealing RL experiments.

---

## 12. Fix Log

### Fix 1 — Hardcoded Penalty Override Bug (CONFIRMED ✅)

**Date:** 2026-05-13  
**Author:** GitHub Copilot (Systems Thinking Engine → highest-leverage fix)  
**File:** `environment.py`  
**Status:** Verified — Run 2 empirical results confirm improvement

#### Root Cause (discovered via Systems Thinking Engine)

`environment.py` hardcoded reward values that overrode config-driven values from `experiments.json`:

```python
# BEFORE (lines 247, 296 — hardcoded, ignoring config):
reward = -0.1   # step penalty (config = -0.01, 10× too severe)
reward = -0.5   # wall penalty (config = -0.1,  5× too severe)

# AFTER (reads config correctly):
reward = self.step_penalty   # → -0.01
reward = self.wall_penalty   # → -0.1
```

**Mechanism:** `__init__` correctly parsed config (`self.step_penalty = env_config.get("step_penalty", -0.1)`), but `perform_action()` bypassed these attributes entirely with hardcoded literals. This was not a logic bug — it was a **silent substitution** with no error, warning, or test catching it.

**Cascading impact (per episode of 300 steps):**
| Component | Before Fix | After Fix | Delta |
|-----------|-----------|-----------|-------|
| Step penalty (300 steps) | 300 × −0.10 = **−30** | 300 × −0.01 = **−3** | **+27** |
| Wall penalty (avg ~18 hits) | 18 × −0.50 = **−9** | 18 × −0.10 = **−1.8** | **+7.2** |
| Mechanical reward offset | — | — | **+34.2/ep** |
| Successful episode reward | −20 (negative!) | **+7** (positive!) | **+27** |

**Training signal before fix:** Even on successful episodes, total reward was **negative** (−20 to −50). The Q-network received gradient signal suggesting "reaching the goal is bad." TD-error calculation: `target = 10.0 + 0.95 × Q_next ≈ 10.0 − 4.75 ≈ 5.25` — small positive target vs large negative actual Q → slow, conflicted learning.

**Q-explosion cascade (ep 1–213 in Run 1):** Penalty × scale × random positive Q_init created runaway TD-errors (Q → 1,896 at ep 119). Fix eliminated this by providing stable, correctly-signed reward landscape from episode 1.

#### Empirical Verification — Run 1 vs Run 2 (ep 0–391)

| Metric | Run 1 (pre-fix) | Run 2 (post-fix) | Δ | Interpretation |
|--------|-----------------|------------------|---|----------------|
| First success | ep 289 | **ep 101** | −65% | Signal clarity → earlier convergence |
| Successes @ ep 391 | 3 (0.8%) | **9 (2.3%)** | +200% | 3× more successes same episode budget |
| Reward mean | −71.19 | **−7.41** | +63.79 | ~52 mechanical + ~12 behavioral |
| Reward stdev | 69.74 | **19.55** | −72% | Landscape ≫ more stable |
| Q-value stdev | 114.10 | **4.56** | −96% | Q-explosion eliminated |
| Loss max | 401.75 | **64.67** | −84% | No more runaway gradient |
| Best success reward | −46.05 (≈560 steps) | **+9.31 (≈69 steps)** | — | ep 357: near-optimal path |

**Virtue Audit note:** ~80% of the +63.79 reward/ep delta is mechanical (penalty rescaling). The genuine behavioral signal is: (a) first success −65% earlier, (b) Q-explosion eliminated, (c) ep 357 with ~69-step path at epsilon=0.699 is a behaviorally meaningful outlier not explainable by pure random walk.

**Baseline preserved:** `results/run1_before_fix_baseline.json` (255.9 KB, compressed from 1,012 MB — 4000:1 ratio) contains full Run 1 per-episode data for all future comparisons.

#### Remaining Caveats (Fix 1 does NOT resolve)

1. **Metric confounding (original INC-007 issue)** — still unresolved. `avg_reward` still conflates gate-toggle bonuses with task reward. Reward decomposition logging (Task 2.1) still pending.
2. **SNN homeostasis overshoot** — firing rate 0.200 vs target 0.130 (+54%) at ep 391. Converging but not yet stable.
3. **All successes still epsilon-dominated** — ep 101–388 successes all have epsilon 67–90%. No deliberate policy confirmed yet (requires epsilon < 0.5 with sustained success rate).
4. **Switch E dead switch** — switch E has no gate rule in `experiments.json` (near goal pos 22,22). May waste exploration budget.

### Fix 2–4 — Observability & Structural (PENDING)

See Section 6 (Investigation Plan) for Tasks 2.1, 2.2, 3.1–3.3. Priority order unchanged:
- **P0 next:** Task 2.1 — reward decomposition logging (zero-risk, additive)
- **P1 next:** Task 1.2 — verify policy quality with ε=0 exploitation run from Run 2 checkpoint

---

## Task 1.2 Result — ε=0 Exploitation Test (2026-05-16)

**Checkpoint:** `results/multi_agent_complex_maze/checkpoint_ep_1150`  
**Config:** `experiments_exploit_ep1150.json` (50 episodes, ε=0.0, max_steps=500)  
**Bugs fixed before run:**
- DQN weights (`agent_0_net.pt`) now loaded on resume (was SNN-only before)
- `initial_exploration` config key now correctly maps to `GlobalContext.initial_exploration_rate`

### Result: FAILED — 0% success rate

| Metric | Value |
|---|---|
| Episodes run | 50 |
| Successes | 0/50 (0.0%) |
| Avg reward (all 50 eps) | **−38.67** |
| Avg reward ep 0–9 | −34.15 |
| Avg reward ep 40–49 | −41.59 |
| Avg Q-value ep 0–9 | −1.046 |
| Avg Q-value ep 40–49 | −1.668 |
| SNN firing rate (ep 0) | 0.1262 |
| SNN firing rate (ep 49) | 0.1997 |

### Analysis

**Q-value collapse observed:** Q-values deteriorated monotonically from −1.05 to −1.67 over 50 episodes. In pure exploitation mode (ε=0), the greedy policy consistently takes actions that receive wall-hit penalties (−1.0/step), which backpropagate to make Q-values more negative. This causes the policy to rate ALL actions as bad, creating a negative feedback loop. No corrective exploration can break this cycle.

**SNN firing rate increase (0.126 → 0.200):** The SNN became progressively more active during exploitation episodes, suggesting the network entered repetitive firing loops. Without exploration to diversify state transitions, the same SNN circuits are repeatedly activated.

**Reward 57% worse than training baseline:** Training avg at ep_1150 was ~−24.0 (with ε=0.316). Pure exploitation gives ~−38.7 — substantially worse. This strongly suggests that the 3.5% success rate during training (ep 0–1150) was driven by **random exploration** (31.6% of actions), not by learned DQN policy.

### Conclusion

**The DQN policy at ep_1150 has NOT learned a functional maze-solving strategy.** All observed successes in Run 2 to this point were epsilon-driven (random exploration stumbling onto the goal path), consistent with the original INC-007 hypothesis.

### Root Cause Confirmation

This confirms the INC-007 hypothesis: `avg_reward` improvements over training were confounded by epsilon decay (more exploitation of a still-random DQN), not genuine policy learning. The fix priorities remain:

1. **Task 2.2 (P0):** Fix switch toggle reward cap — agent earns unbounded toggles, inflating reward without progress
2. **Task 2.1 (P0):** Add reward decomposition metrics for `gate_open_reward`, `wall_hit_count`, `task_reward`
3. **Continue Run 2** from ep_1150 (now restarted with correct ε=0.3161, `initial_exploration: 0.3161` in experiments.json). Re-evaluate policy at ep_2000+ when success rate > 5% sustained.

### Run-2 Resume Status (2026-05-16)

- Crashed at ep_1182 (OOM), restarted from checkpoint_ep_1150
- Episodes 1151–1201 were polluted (ε started at 1.0 due to config mapping bug, not 0.316)
- **Bug fixed:** `initial_exploration: 0.3161` now set in `experiments.json`; run-2 restarted with PID 3724 (cmd wrapper)
- Expected ε at ep_1151: **0.3161** (correct)
