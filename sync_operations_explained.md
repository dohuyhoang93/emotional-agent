# Giải thích chi tiết: Sync Operations và Optimization Options

## Sync là gì?

### Kiến trúc 2 lớp của SNN

```
┌─────────────────────────────────────────────────┐
│  OBJECTS (Python dataclasses)                   │
│  - NeuronState, SynapseState                    │
│  - Chậm (Python loops, object access)           │
│  - Dùng cho: Learning, Checkpoint, Debug        │
│  - Ví dụ: neuron.potential = 0.5                │
└─────────────────────────────────────────────────┘
                    ↕ SYNC
┌─────────────────────────────────────────────────┐
│  TENSORS (NumPy arrays)                         │
│  - t['potentials'], t['thresholds']             │
│  - Nhanh (vectorized operations)                │
│  - Dùng cho: Spike propagation, Homeostasis     │
│  - Ví dụ: t['potentials'] = np.array([...])    │
└─────────────────────────────────────────────────┘
```

### Sync Operations

**`sync_to_tensors()`**: Copy Objects → Tensors
```python
def sync_to_tensors(ctx):
    t = ctx.domain_ctx.tensors
    
    # Copy từ 100 neurons
    for i, neuron in enumerate(ctx.domain_ctx.neurons):
        t['potentials'][i] = neuron.potential      # ← Chậm
        t['thresholds'][i] = neuron.threshold
        t['last_fire_times'][i] = neuron.last_fire_time
    
    # Copy từ ~1500 synapses
    for synapse in ctx.domain_ctx.synapses:
        u, v = synapse.pre_neuron_id, synapse.post_neuron_id
        t['weights'][u, v] = synapse.weight        # ← Chậm
```

**Cost**: ~100-200 μs per call (Python loops)

---

**`sync_from_tensors()`**: Copy Tensors → Objects
```python
def sync_from_tensors(ctx):
    t = ctx.domain_ctx.tensors
    
    # Copy về 100 neurons
    for i, neuron in enumerate(ctx.domain_ctx.neurons):
        neuron.potential = float(t['potentials'][i])      # ← Chậm
        neuron.threshold = float(t['thresholds'][i])
        neuron.last_fire_time = int(t['last_fire_times'][i])
    
    # Copy về ~1500 synapses
    for synapse in ctx.domain_ctx.synapses:
        u, v = synapse.pre_neuron_id, synapse.post_neuron_id
        synapse.weight = float(t['weights'][u, v])        # ← Chậm
```

**Cost**: ~100-200 μs per call (Python loops)

---

## Tại sao cần Sync?

### Workflow hiện tại trong `process_snn_cycle`:

```python
def process_snn_cycle(ctx):
    # 1. PRE-PROCESSING (Object Mode)
    _encode_state_to_spikes_impl(ctx)  # Cập nhật neuron.potential (Objects)
    
    # 2. SYNC Objects → Tensors
    sync_to_tensors(ctx)  # ← SYNC #1 (100-200 μs)
    
    # 3. CORE LOOP (Tensor Mode - FAST)
    _integrate_impl(ctx, sync=False)      # t['potentials'] += input
    _lateral_inhibition_vectorized(ctx)   # t['potentials'] -= inhibition
    _fire_impl(ctx, sync=False)           # spikes = (t['potentials'] > t['thresholds'])
    
    # 4. SYNC Tensors → Objects
    sync_from_tensors(ctx)  # ← SYNC #2 (100-200 μs)
    
    # 5. LEARNING (Object Mode)
    _stdp_3factor_impl(ctx)  # Đọc synapse.weight, neuron.last_fire_time (Objects)
```

**Tại sao cần SYNC #1?**
- `_encode_state_to_spikes_impl` cập nhật `neuron.potential` (Objects)
- Vectorized ops cần đọc từ `t['potentials']` (Tensors)
- → Phải sync Objects → Tensors

**Tại sao cần SYNC #2?**
- Vectorized ops cập nhật `t['potentials']`, `t['last_fire_times']` (Tensors)
- Learning cần đọc `neuron.last_fire_time`, `synapse.weight` (Objects)
- → Phải sync Tensors → Objects

---

## Overhead Analysis

### Hiện tại:
- **2 syncs per timestep** × 11,000 timesteps = **22,000 syncs**
- Mỗi sync: 100-200 μs
- **Total sync overhead**: 2.2-4.4 seconds per experiment

### So với total runtime:
- Episode time: 13s
- Sync overhead: ~2.2-4.4s
- **Sync chiếm ~17-34%** của total time ⚠️

---

## Option 1: Vectorize Encoding

### Ý tưởng:
Chuyển `_encode_state_to_spikes_impl` từ Object mode sang Tensor mode

### Trước (Object Mode):
```python
def _encode_state_to_spikes_impl(ctx):
    observation = ctx.domain_ctx.current_observation  # [16,]
    
    # Loop qua 100 neurons (CHẬM)
    for neuron in ctx.domain_ctx.snn_context.domain_ctx.neurons:
        # Tính similarity
        similarity = np.dot(observation, neuron.prototype_vector)
        
        # Cập nhật potential (Object)
        neuron.potential += similarity * amplification  # ← Object write
```

### Sau (Tensor Mode):
```python
def _encode_state_to_spikes_vectorized(ctx):
    observation = ctx.domain_ctx.current_observation  # [16,]
    t = ctx.domain_ctx.snn_context.domain_ctx.tensors
    
    # Vectorized similarity (NHANH)
    prototypes = t['prototypes']  # (100, 16)
    similarities = prototypes @ observation  # (100,) - Matrix multiply
    
    # Vectorized update (NHANH)
    t['potentials'] += similarities * amplification  # ← Tensor write
```

### Kết quả:
- **Loại bỏ `sync_to_tensors`** (SYNC #1)
- Giảm từ 22,000 → **11,000 syncs** (50% reduction)
- **Speedup dự kiến**: ~1.1-2.2s (8-17% faster)

### Trade-offs:

| Ưu điểm | Nhược điểm |
|---------|------------|
| ✅ 50% ít syncs hơn | ⚠️ Cần refactor `_encode_state_to_spikes_impl` |
| ✅ Code nhanh hơn (vectorized) | ⚠️ Phức tạp hơn (tensor indexing) |
| ✅ Vẫn giữ learning ở Object mode | ⚠️ Vẫn còn 11,000 syncs (SYNC #2) |

---

## Option 2: Lazy Sync (Aggressive)

### Ý tưởng:
Chỉ sync khi **thực sự cần**, không sync mỗi timestep

### Implementation:

```python
def process_snn_cycle(ctx):
    # 1. PRE-PROCESSING (Object Mode)
    _encode_state_to_spikes_impl(ctx)
    
    # 2. SYNC Objects → Tensors (CONDITIONAL)
    if ctx.domain_ctx.snn_context.domain_ctx.current_time % 10 == 0:
        sync_to_tensors(ctx)  # Chỉ sync mỗi 10 timesteps
    
    # 3. CORE LOOP (Tensor Mode)
    _integrate_impl(ctx, sync=False)
    _lateral_inhibition_vectorized(ctx)
    _fire_impl(ctx, sync=False)
    
    # 4. SYNC Tensors → Objects (CONDITIONAL)
    if ctx.domain_ctx.snn_context.domain_ctx.current_time % 10 == 0:
        sync_from_tensors(ctx)  # Chỉ sync mỗi 10 timesteps
    
    # 5. LEARNING (Object Mode - Đọc stale data)
    _stdp_3factor_impl(ctx)  # ⚠️ Đọc data cũ 10 timesteps
```

### Kết quả:
- Giảm từ 22,000 → **2,200 syncs** (90% reduction)
- **Speedup dự kiến**: ~2.0-4.0s (15-30% faster)

### Trade-offs:

| Ưu điểm | Nhược điểm |
|---------|------------|
| ✅ 90% ít syncs hơn | ❌ Learning đọc stale data (lag 10 steps) |
| ✅ Đơn giản (chỉ thêm if) | ❌ Có thể ảnh hưởng learning quality |
| ✅ Speedup lớn nhất | ❌ Checkpoint cần sync thủ công |

---

## Option 3: Hybrid (Khuyến nghị)

### Ý tưởng:
Kết hợp Option 1 + Lazy sync cho learning

### Implementation:

```python
def process_snn_cycle(ctx):
    # 1. PRE-PROCESSING (Tensor Mode - Vectorized)
    _encode_state_to_spikes_vectorized(ctx)  # ← Option 1
    # → Không cần sync_to_tensors
    
    # 2. CORE LOOP (Tensor Mode)
    _integrate_impl(ctx, sync=False)
    _lateral_inhibition_vectorized(ctx)
    _fire_impl(ctx, sync=False)
    
    # 3. SYNC Tensors → Objects (CONDITIONAL)
    if ctx.domain_ctx.snn_context.domain_ctx.current_time % 5 == 0:
        sync_from_tensors(ctx)  # Sync mỗi 5 timesteps cho learning
    
    # 4. LEARNING (Object Mode)
    if ctx.domain_ctx.snn_context.domain_ctx.current_time % 5 == 0:
        _stdp_3factor_impl(ctx)  # Learning mỗi 5 timesteps
```

### Kết quả:
- **Loại bỏ hoàn toàn SYNC #1** (sync_to_tensors)
- **Giảm SYNC #2** từ 11,000 → 2,200 (mỗi 5 timesteps)
- **Total syncs**: 0 + 2,200 = **2,200 syncs** (90% reduction)
- **Speedup dự kiến**: ~2.5-4.0s (19-30% faster)

### Trade-offs:

| Ưu điểm | Nhược điểm |
|---------|------------|
| ✅ 90% ít syncs hơn | ⚠️ Cần refactor encoding (medium effort) |
| ✅ Learning vẫn chạy (mỗi 5 steps) | ⚠️ Learning frequency giảm (có thể OK) |
| ✅ Speedup lớn | ⚠️ Cần test learning quality |
| ✅ Cân bằng tốt nhất | |

---

## So sánh tổng quan

| Metric | Baseline | Option 1 | Option 2 | Option 3 |
|--------|----------|----------|----------|----------|
| **Syncs/experiment** | 22,000 | 11,000 | 2,200 | 2,200 |
| **Speedup dự kiến** | 0s | 1.1-2.2s | 2.0-4.0s | 2.5-4.0s |
| **Episode time** | 13s | ~11s | ~10s | ~9.5s |
| **Code complexity** | Low | Medium | Low | Medium |
| **Learning quality** | ✅ | ✅ | ⚠️ | ✅ |
| **Effort** | - | Medium | Low | Medium |

---

## Khuyến nghị

**Chọn Option 3 (Hybrid)** vì:
1. **Speedup tốt nhất** (~30% faster)
2. **Không ảnh hưởng learning** (vẫn chạy mỗi 5 steps)
3. **Cân bằng** giữa performance và correctness

**Roadmap**:
1. Implement Option 1 trước (vectorize encoding)
2. Test để verify correctness
3. Thêm lazy sync cho learning (Option 3)
4. Tune learning frequency (5, 10, hoặc 20 steps)
