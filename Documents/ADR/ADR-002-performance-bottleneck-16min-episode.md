# ADR-002: Performance Bottleneck — 16 phút/episode

**Date**: 2026-03-11  
**Status**: Open  
**Context**: EmotionAgent — 1 episode × 500 steps × 5 agents mất ~960 giây

---

## Kết quả Profiling (1024 neurons, connectivity=0.1)

```
Từng process trong pipeline (avg per call):
  process_snn_cycle (FULL)        271.99 ms   ← ĐÂY LÀ CHÍNH
  process_homeostasis             105.77 ms   ← #2
  process_commitment              114.62 ms   ← #3
  select_action_gated               2.25 ms
  process_neural_darwinism          0.01 ms   ← tốt (đã tắt hầu hết)
  process_periodic_resync           0.01 ms

Chi tiết bên trong SNN cycle (per tick):
  _stdp_3factor_impl               50.86 ms   ← BOTTLENECK THỰC SỰ
  _integrate_impl                   0.02 ms
  _fire_impl                        0.04 ms
  _lateral_inhibition               0.00 ms
  sync_to_heavy_tensors             0.89 ms
```

### Tính toán

| Giai đoạn | Thời gian/step | Tỷ lệ |
|---|---|---|
| `_stdp_3factor` × 10 ticks | 508.6 ms | **~68%** |
| `process_homeostasis` | 105.8 ms | ~14% |
| `process_commitment` | 114.6 ms | ~15% |
| `_integrate` × 10 ticks | 0.2 ms | ~0% |
| Rest | ~50 ms | ~3% |
| **Total/step** | **~780 ms** | |

**Episode estimate**: 780ms × 500 steps = **390s** lý thuyết  
**Overhead thực tế**: 960s / 390s ≈ **2.5x** overhead từ Theus transaction + `engine.edit()` + Python GIL trong ThreadPoolExecutor

---

## Root Cause: `_stdp_3factor_impl`

STDP (Spike-Timing-Dependent Plasticity) 3-factor learning cập nhật **weight matrix (N × N = 1024 × 1024)** mỗi tick:

```python
# snn_learning_3factor_theus.py
# O(N²) weight update — 1,048,576 phép tính mỗi tick × 10 ticks/step
```

Không có conditional skip: ngay cả khi không có spike, STDP vẫn chạy.

**Homeostasis (105ms)** và **Commitment (114ms)** cũng iterate qua 1024 neuron objects (Python loop, không vectorized).

---

## Tác động thực tế

- 1 episode × 1 agent: ~390s (6.5 phút)
- 1 episode × 5 agents PARALLEL: ~390s (GIL trong 5 threads → không thực sự parallel)
- 5000 episodes: **390s × 5000 = 543 giờ (~22 ngày)**

---

## Giải pháp đề xuất (theo mức ưu tiên)

### Option A: Skip STDP khi không có spikes [NHANH, ít rủi ro]

```python
# _stdp_3factor_impl: thêm điều kiện
fired_indices = np.where(can_fire)[0]
if len(fired_indices) == 0:
    return {}   # Skip toàn bộ STDP nếu không có spike
```

Với `firing_rate = 0.069` → chỉ ~70/1024 neurons fire → STDP 93% thời gian là vô ích nếu làm full matrix.

### Option B: Vectorize homeostasis + commitment [TRUNG BÌNH]

Thay Python loop trên 1024 objects bằng tensor operations:
```python
# Thay vì: for neuron in neurons: neuron.threshold *= factor
thresholds = t['thresholds']
thresholds *= factor  # vectorized, ~0.01ms thay vì 100ms
```

### Option C: Giảm `num_neurons` và `ticks_per_step` để test [TẠM THỜI]

```json
// experiments.json
"num_neurons": 256,          // 256 thay vì 1024 → giảm 16× memory
"ticks_per_step": 3,         // 3 thay vì 10 → giảm 3× thời gian
```

Ước tính: 780ms → ~45ms/step → 22.5s/episode → 5000 eps = **31 giờ** (khả thi hơn nhưng vẫn dài)

### Option D: STDP chỉ cập nhật sparse weights [DÀI HẠN]

Chỉ update (i, j) khi neuron i hoặc j thực sự fired:
```python
# Thay vì full N×N update → chỉ K×N với K = số neurons fired
# Với K ≈ 70, N = 1024: 71,680 phép tính thay vì 1,048,576 (~14× faster)
```

---

## Files liên quan

- [`snn_learning_3factor_theus.py`](file:///c:/Users/dohoang/projects/EmotionAgent/src/processes/snn_learning_3factor_theus.py) — `_stdp_3factor_impl()`
- [`snn_homeostasis_theus.py`](file:///c:/Users/dohoang/projects/EmotionAgent/src/processes/snn_homeostasis_theus.py) — `process_homeostasis()`
- [`snn_commitment_theus.py`](file:///c:/Users/dohoang/projects/EmotionAgent/src/processes/snn_commitment_theus.py) — `process_commitment()`
- [`snn_composite_theus.py`](file:///c:/Users/dohoang/projects/EmotionAgent/src/processes/snn_composite_theus.py) — `ticks_per_step = 10` (line 68)
- [`profile_pipeline.py`](file:///c:/Users/dohoang/projects/EmotionAgent/profile_pipeline.py) — Script profiling để tái hiện kết quả
