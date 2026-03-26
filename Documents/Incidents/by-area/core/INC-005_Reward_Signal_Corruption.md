# INC-005: Reward Signal Corruption — "Intrinsic Decoupling" và "Epsilon Lock" trong SNNs-MLP

**Date:** 2026-03-20  
**Component:** `src/processes/snn_rl_bridge.py` · `src/processes/rl_processes.py` · `src/orchestrator/processes/p_decay_exploration.py`  
**Severity:** Critical (Learning Plateau / Signal Corruption)  
**Author:** Do Huy Hoang  
**Status:** Open  

---

## 1. Executive Summary

Sau **749 episodes** thực nghiệm `multi_agent_complex_maze` (5 agents, mê cung 25×25, 4 dynamic gates), hệ thống thể hiện **Learning Plateau** hoàn toàn từ episode 300 trở đi: `avg_reward` giữ nguyên trong khoảng −77 đến −80, `success_rate` chỉ đạt 5.6% sau 3/4 số episode dự kiến, và hầu như không có breakthrough từ ep504.

Điều tra pháp y xác định nguyên nhân **không phải** ở kiến trúc SNN hay độ phức tạp của mê cung, mà là **2 Reinforcing Loops tự duy trì nhau**, phát sinh từ hai lỗi thiết kế riêng biệt nhưng tương hỗ lẫn nhau:

1. **R1 — "Intrinsic Decoupling"**: `compute_intrinsic_reward_snn` trả về giá trị cứng `0.5` khi không có neuron active → Episode thất bại có `R_net = +5.5` (dương!).
2. **R2 — "Epsilon Lock"**: Epsilon bị reset về `1.0` sau mỗi lần resume → Agent không bao giờ đạt phase khai thác (exploit).

---

## 2. Background

Thực nghiệm `multi_agent_complex_maze` được thiết kế để kiểm chứng khả năng học tập dài hạn của hệ thống SNN-RL với:
- Grid size: 25×25
- 5 switches (A→E) điều khiển 4 dynamic gates
- 5 agents hoạt động song song
- Mục tiêu: Tất cả agents học tìm đường từ (0,0) đến (24,24)

**Config reward chính:**
| Sự kiện | Reward |
|---------|--------|
| Đạt đích | +10.0 |
| Mở gate | +1.0 |
| Đóng gate | −1.2 |
| Mỗi bước | −0.01 |
| Đâm tường | −0.1 |
| Timeout | −2.0 |

**Intrinsic reward** được pha trộn theo công thức tuyến tính:  
`R_total = R_ext + 0.05 × novelty + 0.05 × |TD_error|`

---

## 3. What Went Wrong

### Bug A — `compute_intrinsic_reward_snn`: Default silently breaks signal hierarchy

**File:** `src/processes/snn_rl_bridge.py`, dòng 454–456

```python
if not active_vectors:
    return {'intrinsic_reward': 0.5}   # ← BUG: "neutral" thực ra là BONUS
```

Khi SNN không có neuron nào active (trường hợp phổ biến ở đầu episode), hàm trả về `novelty = 0.5`. Đây không phải "neutral" — đây là **điểm dương tích lũy**:

```
500 steps × 0.05 weight × 0.5 novelty = +12.5 điểm intrinsic / episode
Episode thất bại: R_ext = −7.0  →  R_net = +5.5  [DƯƠNG → Agent được khen vì thất bại]
```

**Tỷ lệ signal/noise thực tế:**
- Goal reward per step: `10.0 / 500 = 0.020`
- Intrinsic per step (bug): `0.05 × 0.5 = 0.025`
- **Noise (0.025) > Signal (0.020)** — Agent mù màu với mục tiêu dài hạn.

---

### Bug B — Epsilon không được bảo toàn khi resume từ checkpoint

**File:** `src/orchestrator/processes/p_decay_exploration.py` (không lưu epsilon vào checkpoint)  
**File:** `src/orchestrator/processes/p_initialize_experiment.py` (không load epsilon từ checkpoint)

Thực nghiệm đã bị **restart ít nhất 3 lần** (phát hiện qua epsilon reset về `0.999` tại ep≈200, ep≈500 trong metrics). Mỗi restart:
- Epsilon = `1.0` (khởi đầu lại từ đầu)
- Với `decay_rate = 0.999`, cần **3,000 episodes liên tục** để epsilon < `0.05`
- Mỗi chu kỳ chỉ có ~250 episodes → epsilon cuối chu kỳ ≈ `0.779`

**Hiệu ứng compound:** `select_action_gated` tăng epsilon thêm theo emotion magnitude:

```python
adjusted_exploration = current_exploration_rate * (1.0 + 0.5 * emotion_magnitude)
# emotion_magnitude ≈ 1.0 (khi SNN active)
# → adjusted_eps = 0.779 × 1.5 = 1.0 (CLIPPED)
```

**Kết luận:** Mọi bước có SNN active = **100% random action**. Agent không bao giờ exploit Q-values đã học.

---

## 4. Root Cause Analysis

### Micro Root Cause (Mental Model Error)

Thiết kế `intrinsic_reward = 0.5` khi im lặng xuất phát từ tư duy **"neutral là an toàn"**. Tuy nhiên trong bối cảnh RL, không có neutral reward — mọi giá trị không âm đều là tín hiệu reward ngầm. Mô hình tư duy sai: *"0.5 = không có thông tin"* thực ra là *"0.5 = tồn tại là đủ"*.

Tương tự, không lưu epsilon vào checkpoint xuất phát từ tư duy **"chỉ cần lưu weights là đủ"** — bỏ qua rằng exploration policy là trạng thái học tập không kém phần quan trọng so với network weights.

### Macro Root Cause (Structural / Feedback Loop)

```
══════════════════════════════════════════════════════════
R1: INTRINSIC DECOUPLING (tự duy trì, không cần trigger)
══════════════════════════════════════════════════════════
SNN ít active → novelty = 0.5 (bug)
      ↓
R_net = R_ext + 12.5 → dương dù thất bại
      ↓
Q-network học: "thất bại = OK" → không cần tìm đích
      ↓ ←───────────────────────────────────────┐
Không có áp lực goal → SNN tiếp tục ít active ──┘

══════════════════════════════════════════════════════════
R2: EPSILON LOCK (restart driven, được R1 nuôi dưỡng)
══════════════════════════════════════════════════════════
Restart → epsilon = 1.0 → random actions 100%
      ↓
R_ext âm → nhưng R_total dương nhờ R1
      ↓
Q-values lệch → SNN active nhiều hơn → emotion_mag ≈ 1.0
      ↓ ←───────────────────────────────────────┐
adjusted_eps = 1.0 (clip) → random mãi ──────────┘
```

**R1 và R2 cộng hưởng**: R1 "bù đắp" hậu quả tiêu cực của R2 → hệ thống không có tín hiệu tự nhiên để thoát khỏi vòng lặp.

---

## 5. Impact Assessment

| Khía cạnh | Mức độ ảnh hưởng |
|-----------|-----------------|
| Learning convergence | **Bị chặn hoàn toàn** — không có cơ chế nội tại để thoát plateau |
| Episode thành công | Chỉ 25/749 breakthroughs (~3.3%), tất cả đều ngẫu nhiên (random walk may mắn) |
| Tài nguyên tính toán | ~749 episodes × 500 steps × 5 agents chạy không có hiệu quả học tập thực sự |
| Scientific validity | Kết quả thực nghiệm hiện tại **không thể** được dùng để đánh giá năng lực học tập SNN |

---

## 6. Resolution

### Fix 1 — Sửa intrinsic reward default [PRIORITY: P0]

```python
# File: src/processes/snn_rl_bridge.py, dòng 454–456
# TRƯỚC:
if not active_vectors:
    return {'intrinsic_reward': 0.5}

# SAU:
if not active_vectors:
    # NOTE: Trả về 0.0 thay vì 0.5 — im lặng của SNN không nên được thưởng.
    # Chỉ có novelty thực sự (từ neuron active) mới tạo ra intrinsic reward.
    return {'intrinsic_reward': 0.0}
```

**Kết quả kỳ vọng:** R_net episode thất bại từ `+5.5` → `−7.0` (đúng bản chất).

### Fix 2 — Bảo toàn epsilon qua checkpoint [PRIORITY: P0]

```python
# File: src/orchestrator/processes/p_save_checkpoint.py
# Thêm vào dữ liệu checkpoint:
checkpoint_data['exploration_rates'] = {
    str(i): agent.rl_ctx.domain_ctx.current_exploration_rate
    for i, agent in enumerate(coordinator.agents)
}

# File: src/orchestrator/processes/p_initialize_experiment.py
# Khi load checkpoint, restore epsilon:
if 'exploration_rates' in checkpoint_data:
    for i, agent in enumerate(coordinator.agents):
        restored_eps = checkpoint_data['exploration_rates'].get(str(i), 1.0)
        agent.rl_ctx.domain_ctx.current_exploration_rate = restored_eps
```

### Fix 3 — Clamp emotion boost factor [PRIORITY: P1]

```python
# File: src/processes/rl_processes.py, dòng 177
# TRƯỚC:
adjusted_exploration = ctx.domain_ctx.current_exploration_rate * (1.0 + 0.5 * emotion_magnitude)
# SAU:
# NOTE: Factor 0.5 gây clip về 1.0 quá thường xuyên khi SNN active.
# 0.2 vẫn giữ tính năng emotion-driven exploration nhưng tránh lock ở 100%.
adjusted_exploration = ctx.domain_ctx.current_exploration_rate * (1.0 + 0.2 * emotion_magnitude)
```

### Fix 4 — Căn chỉnh target_fire_rate [PRIORITY: P2]

```json
// File: experiments.json, tham số snn_config
// TRƯỚC:
"target_fire_rate": 0.01

// SAU:
// NOTE: Thực tế quan sát avg_firing_rate ≈ 0.133.
// target=0.01 khiến homeostasis liên tục push threshold lên, gây tug-of-war với
// input_amplification=20. Căn chỉnh về 0.13 giải phóng cơ chế cân bằng.
"target_fire_rate": 0.13
```

---

## 7. Verification

Script kiểm chứng: `tests/repro_INC005_reward_signal.py`

**Kiểm tra cần pass sau khi sửa:**
1. Episode thất bại (hết timeout): `R_net < 0` (không còn dương giả)
2. Epsilon sau resume từ checkpoint: giữ nguyên giá trị đã decay (không reset về 1.0)
3. `adjusted_eps` với `em=1.0`, `eps=0.779`: kết quả ≤ `0.95` (không clip về 1.0)

---

## 8. Preventive Actions

1. **Unit test** cho `compute_intrinsic_reward_snn`: `assert novelty == 0.0 when no neurons active`
2. **Checkpoint schema validation**: thêm `exploration_rates` vào required fields của checkpoint
3. **Monitoring alert**: Nếu `avg_reward` không thay đổi > 50 episodes liên tiếp → cảnh báo plateau
4. **ADR**: Ghi lại nguyên tắc "Intrinsic reward không được dương khi SNN im lặng" trong Architecture Decision Records

---

## 9. Related

- **Phân tích metrics**: `brain/56414aa3.../snn_performance_analysis.md`
- **Systems Thinking Analysis**: `brain/56414aa3.../systems_thinking_analysis.md`
- **Test code chứng minh**: `EmotionAgent/test_hypotheses.py`
- **INC-001**: Zero Firing Rate SNN (tiền thân của vấn đề homeostasis)
