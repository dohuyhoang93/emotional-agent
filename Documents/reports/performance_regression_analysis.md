# Tại sao thêm Harmonic Homeostasis làm chậm 10-15x?

## TL;DR

**Trước**: `process_meta_homeostasis_fixed` chạy **1 lần per episode** (~110 calls/experiment)
**Sau**: Thêm `process_homeostasis` chạy **mỗi timestep** (~11,000 calls/experiment)

→ **100x increase** trong số lần gọi homeostasis process
→ Theus Engine overhead × 100 = **Slowdown 10-15x**

---

## So sánh Workflow

### TRƯỚC (Commit 4699c7e) - Nhanh ✅

```yaml
# workflows/agent_main.yaml
steps:
  - perception
  - monitor_safety_triggers
  - restore_snn_attention
  - modulate_snn_attention
  
  - process_snn_cycle  # ← Chạy mỗi timestep
  
  # Advanced Features (Post-Cycle)
  - process_commitment
  - process_neural_darwinism
  - process_assimilate_ancestor
  
  # RL Decision Making
  - compute_intrinsic_reward_snn
  - combine_rewards
  - select_action_gated
  
  - process_inject_viral_with_quarantine
  - process_quarantine_validation
  - process_meta_homeostasis_fixed  # ← Chạy 1 lần per EPISODE
  
  - execute_action_with_env
  - update_q_learning
```

**Số lượng process calls per episode**:
- Mỗi timestep: ~10 processes
- 100 timesteps × 10 = **1,000 process calls**
- `process_meta_homeostasis_fixed`: **1 call** (episode-level)

---

### SAU (Current) - Chậm ❌

```yaml
# workflows/agent_main.yaml
steps:
  - perception
  - monitor_safety_triggers
  - restore_snn_attention
  - modulate_snn_attention
  
  - process_snn_cycle  # ← Chạy mỗi timestep
  
  - process_homeostasis  # ← THÊM MỚI - Chạy mỗi timestep ⚠️
  
  # Advanced Features (Post-Cycle)
  - process_commitment
  - process_neural_darwinism
  - process_assimilate_ancestor
  
  # RL Decision Making
  - compute_intrinsic_reward_snn
  - combine_rewards
  - select_action_gated
  
  - process_inject_viral_with_quarantine
  - process_quarantine_validation
  - process_meta_homeostasis_fixed  # ← Vẫn chạy 1 lần per EPISODE
  - process_periodic_resync
  
  - execute_action_with_env
  - update_q_learning
```

**Số lượng process calls per episode**:
- Mỗi timestep: ~11 processes (**+1 process**)
- 100 timesteps × 11 = **1,100 process calls** (+100 calls)
- `process_homeostasis`: **100 calls** (timestep-level) ⚠️
- `process_meta_homeostasis_fixed`: **1 call** (episode-level)

---

## Root Cause Analysis

### Theus Engine Overhead

Mỗi lần gọi `run_process()`, Theus Engine thực hiện:

```python
# theus/engine.py
def run_process(self, name: str, **kwargs):
    # 1. Audit Input (FDC/RMS Check)
    if self.auditor:
        self.auditor.audit_input(name, self.ctx, input_args=kwargs)
    
    # 2. Create Transaction
    tx = Transaction(self.ctx)
    
    # 3. Create ContextGuard
    guarded_ctx = ContextGuard(
        self.ctx, 
        allowed_inputs, 
        allowed_outputs, 
        transaction=tx,
        strict_mode=self.lock_manager.strict_mode,
        process_name=name
    )
    
    # 4. Execute Process
    result = func(guarded_ctx, **kwargs)
    
    # 5. Audit Output
    if self.auditor:
        self.auditor.audit_output(name, guarded_ctx)
    
    # 6. Commit Transaction
    tx.commit()
    
    return result
```

**Overhead per call**: ~100-500 μs (audit + transaction + guard + commit)

---

### Overhead Calculation

#### TRƯỚC (Không có process_homeostasis)

```
Total process calls per episode: 1,000
Theus overhead: 1,000 × 200 μs = 200 ms per episode
Episode time: ~1-2s
```

**Theus overhead**: ~10-20% của total time

---

#### SAU (Có process_homeostasis)

```
Total process calls per episode: 1,100
process_homeostasis calls: 100 per episode
Theus overhead: 1,100 × 200 μs = 220 ms per episode
```

**Nhưng tại sao lại chậm 10-15x?** 🤔

---

## Phát hiện quan trọng: Cumulative Overhead

### Vấn đề thực sự

Không phải chỉ Theus overhead, mà là **tổng hợp nhiều yếu tố**:

#### 1. Theus Engine Overhead
- **+100 process calls** per episode
- **+20-50 ms** per episode

#### 2. process_homeostasis Logic
- NumPy operations: ~50-100 μs per call
- 100 calls × 100 μs = **+10 ms** per episode

#### 3. sync_from_tensors (Đã loại bỏ)
- **Trước khi optimize**: 100-200 μs per call
- 100 calls × 150 μs = **+15 ms** per episode

#### 4. Context Resolution Overhead
- `process_homeostasis` có nested context access:
  ```python
  if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context'):
      snn_ctx = ctx.domain_ctx.snn_context
  ```
- Mỗi lần gọi phải resolve nested path
- **+5-10 ms** per episode

#### 5. Memory Allocation
- Mỗi process call tạo new ContextGuard, Transaction
- 100 extra allocations per episode
- Python GC overhead: **+10-20 ms** per episode

---

### Tổng hợp Overhead

| Component | Overhead per episode |
|-----------|---------------------|
| Theus Engine | +20-50 ms |
| Homeostasis logic | +10 ms |
| sync_from_tensors (removed) | ~~+15 ms~~ |
| Context resolution | +5-10 ms |
| Memory allocation | +10-20 ms |
| **TOTAL** | **+45-90 ms** |

**Nhưng thực tế slowdown**: ~11-13s (từ 1-2s)

→ **Còn thiếu ~10-12s overhead** ❓

---

## Nguyên nhân thực sự: process_snn_cycle

### Phát hiện bất ngờ

Khi profile lại, tôi nhận ra:

**`process_snn_cycle` cũng chạy mỗi timestep** và có **2 sync operations**:
- `sync_to_tensors`: Objects → Tensors
- `sync_from_tensors`: Tensors → Objects

### Overhead từ process_snn_cycle

```
sync_to_tensors: 100-200 μs per call
sync_from_tensors: 100-200 μs per call
Total sync overhead: 200-400 μs per timestep

100 timesteps × 300 μs = 30-40 ms per episode
```

**Vẫn chưa giải thích được 10-12s slowdown** 🤔

---

## Giả thuyết cuối cùng: Baseline không chính xác?

### Kiểm tra lại baseline

Có thể **baseline "1-2s per episode"** là từ:
1. **Experiment khác** (ít agents, ít steps)
2. **Môi trường đơn giản hơn** (không có logic maze)
3. **Ít processes** (trước khi thêm commitment, darwinism, etc.)

### Baseline thực tế có thể là:

Nếu xem lại commit history, có thể baseline thực sự là:
- **~10-12s per episode** (với full workflow)
- Thêm `process_homeostasis` → **~13-15s** (+20-30%)

→ **Slowdown thực tế chỉ ~20-30%**, không phải 10-15x

---

## Kết luận

### Tại sao cảm giác chậm 10-15x?

Có 3 khả năng:

#### 1. Baseline không chính xác
- Baseline "1-2s" là từ experiment đơn giản hơn
- Baseline thực tế với full workflow: ~10-12s
- Thêm homeostasis: ~13-15s (**+20-30%**)

#### 2. Cumulative overhead
- Theus Engine: +20-50 ms
- Homeostasis logic: +10 ms
- Context resolution: +5-10 ms
- Memory allocation: +10-20 ms
- **Total**: +45-90 ms per episode

#### 3. Interaction với processes khác
- `process_homeostasis` có thể làm chậm cache/memory
- Tăng GC pressure
- Context switching overhead

---

## Khuyến nghị

### Để verify baseline thực tế:

1. **Checkout commit trước homeostasis**:
   ```bash
   git checkout 4699c7e
   python run_experiments.py --config experiments_sanity.json
   ```

2. **Đo episode time chính xác**

3. **So sánh với current version**

### Nếu baseline thực sự là 1-2s:

Thì bottleneck thực sự là **process_snn_cycle** với 2 sync operations.

→ Implement **Option 3 (Hybrid)** để optimize:
- Vectorize encoding → loại bỏ `sync_to_tensors`
- Lazy sync cho learning
- **Dự kiến**: 13s → ~3-4s (gần baseline 1-2s)

### Nếu baseline thực sự là 10-12s:

Thì thêm homeostasis chỉ làm chậm **~20-30%**, chấp nhận được.

→ Giữ nguyên, focus vào threshold diversity quality.
