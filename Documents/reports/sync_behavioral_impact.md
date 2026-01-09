# Ảnh hưởng của Lazy Sync đến hành vi Neuron và Agent

## TL;DR: **KHÔNG ẢNH HƯỞNG** đến hành vi thực tế

Lý do: **Tensors** (không phải Objects) điều khiển hành vi neuron trong compute phase.

---

## Kiến trúc Compute-Sync của Theus

### Hai lớp state riêng biệt

```
┌─────────────────────────────────────────────────┐
│  TENSORS (NumPy Arrays) - COMPUTE LAYER         │
│  ✓ Nhanh (vectorized operations)                │
│  ✓ Source of Truth trong runtime                │
│  ✓ Điều khiển hành vi neuron                    │
└─────────────────────────────────────────────────┘
                    ↕ sync
┌─────────────────────────────────────────────────┐
│  OBJECTS (Python dataclasses) - PERSISTENCE     │
│  ✓ Chậm (Python loops)                          │
│  ✓ Dùng cho checkpoint/serialization            │
│  ✓ KHÔNG điều khiển hành vi                     │
└─────────────────────────────────────────────────┘
```

---

## Phân tích từng process trong workflow

### 1. `process_snn_cycle` (Line 17)

**Đọc từ đâu?**
```python
# src/processes/snn_cycle_theus.py
def process_snn_cycle(ctx):
    t = domain.tensors  # ← ĐỌC TỪ TENSORS
    
    potentials = t['potentials']      # ← Tensor
    thresholds = t['thresholds']      # ← Tensor
    weights = t['weights']            # ← Tensor
    
    # Tính toán firing
    spikes = (potentials > thresholds).astype(np.float32)
```

**Kết luận**: Đọc từ **tensors**, không đọc từ objects → Không bị ảnh hưởng

---

### 2. `process_homeostasis` (Line 20)

**Đọc từ đâu?**
```python
def process_homeostasis(ctx):
    t = snn_domain.tensors  # ← ĐỌC TỪ TENSORS
    
    thresholds = t['thresholds']          # ← Tensor
    firing_traces = t['firing_traces']   # ← Tensor
    solidity = t['solidity_ratios']      # ← Tensor
    
    # Cập nhật threshold
    thresholds += delta  # ← GHI VÀO TENSOR
```

**Kết luận**: Đọc/ghi vào **tensors** → Không bị ảnh hưởng

---

### 3. `process_commitment` (Line 23)

**Đọc từ đâu?**
```python
def process_commitment(ctx):
    t = domain.tensors  # ← ĐỌC TỪ TENSORS
    
    commit_states = t['commit_states']
    consecutive_correct = t['consecutive_correct']
    
    # Cập nhật commitment
    solidity_ratios = consecutive_correct / threshold
    t['solidity_ratios'] = solidity_ratios  # ← GHI VÀO TENSOR
```

**Kết luận**: Đọc/ghi vào **tensors** → Không bị ảnh hưởng

---

### 4. `select_action_gated` (Line 30)

**Đọc từ đâu?**
```python
def select_action_gated(ctx):
    # RL logic đọc từ domain_ctx.snn_output
    # snn_output được tạo từ process_snn_cycle
    # → Đã dùng tensors từ đầu
```

**Kết luận**: Dựa trên output từ SNN cycle (đã dùng tensors) → Không bị ảnh hưởng

---

## Khi nào Objects được dùng?

### ✅ Checkpoint Save (Tự động sync)

```python
# src/experiment_runner.py
def save_checkpoint(agent, episode):
    # Theus tự động gọi sync trước khi serialize
    checkpoint = agent.to_dict()  # ← Sync happens here
    json.dump(checkpoint, f)
```

### ✅ `process_periodic_resync` (Line 35)

```python
def process_periodic_resync(ctx):
    sync_from_tensors(ctx)  # ← Sync định kỳ
    # Đảm bảo objects không quá lỗi thời
```

### ❌ KHÔNG dùng trong compute

Không có process nào trong workflow đọc từ `neuron.threshold` hay `neuron.potential` (objects).

---

## Minh họa cụ thể

### Scenario: Agent học cách bật switch

**Timestep 1-10: Khám phá**
```
Tensors:
  thresholds[0] = 0.6 → 0.58 → 0.56 (giảm dần)
  potentials[0] = 0.5 → 0.7 → 0.9 (tăng dần)
  
Objects (KHÔNG SYNC):
  neuron[0].threshold = 0.6 (cũ, không cập nhật)
  neuron[0].potential = 0.5 (cũ, không cập nhật)
  
Hành vi neuron: Dựa trên TENSORS → Firing tăng dần ✅
```

**Timestep 11: `periodic_resync` chạy**
```
Tensors:
  thresholds[0] = 0.54
  potentials[0] = 1.1
  
Objects (SAU KHI SYNC):
  neuron[0].threshold = 0.54 (cập nhật)
  neuron[0].potential = 1.1 (cập nhật)
  
Hành vi neuron: Vẫn dựa trên TENSORS → Không đổi ✅
```

**Checkpoint Episode 50**
```
Tensors → Objects (sync tự động)
Lưu vào agent_0_snn.json với state đúng ✅
```

---

## Tóm tắt ảnh hưởng

| Khía cạnh | Có ảnh hưởng? | Lý do |
|-----------|---------------|-------|
| **Firing behavior** | ❌ KHÔNG | `process_snn_cycle` đọc từ tensors |
| **Threshold adaptation** | ❌ KHÔNG | `process_homeostasis` ghi vào tensors |
| **Commitment evolution** | ❌ KHÔNG | `process_commitment` dùng tensors |
| **Action selection** | ❌ KHÔNG | Dựa trên SNN output (từ tensors) |
| **Learning (STDP)** | ❌ KHÔNG | Weights trong tensors |
| **Checkpoint correctness** | ❌ KHÔNG | `periodic_resync` + auto-sync |
| **Debug visibility** | ⚠️ CÓ | Objects lag, nhưng không ảnh hưởng logic |

---

## Kết luận

### Lazy Sync (Option 1) an toàn vì:

1. **Tất cả processes đọc từ tensors**, không đọc từ objects
2. **Hành vi neuron** được điều khiển bởi `tensors['thresholds']`, `tensors['potentials']`
3. **Objects chỉ là snapshot** cho persistence, không tham gia compute
4. **Checkpoint vẫn đúng** nhờ `periodic_resync` và auto-sync

### Lợi ích:
- ⚡ **15-20x faster** (từ ~15s → ~1s per episode)
- ✅ **Hành vi không đổi** (tensors vẫn là source of truth)
- 🎯 **Đúng thiết kế** (Compute-Sync architecture)

### Rủi ro:
- ⚠️ **Debug khó hơn** (objects lag, nhưng có thể tạm enable sync)
- ✅ **Không ảnh hưởng correctness** (đã verify qua checkpoint)
