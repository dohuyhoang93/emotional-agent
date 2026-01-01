# So sánh Option 1 vs Option 2: Tối ưu sync_from_tensors

## Bối cảnh

Hiện tại: `process_homeostasis` gọi `sync_from_tensors()` **mỗi timestep**
- 100 steps/episode × 110 episodes = **11,000 calls**
- Mỗi call: ~100 neuron updates + ~1,500 synapse updates
- **Tổng: ~16.5 triệu object updates** → Bottleneck chính

---

## Option 1: Lazy Sync (Loại bỏ hoàn toàn)

### Thay đổi

```python
# src/processes/snn_homeostasis_theus.py
def process_homeostasis(ctx: SNNSystemContext):
    # ... (logic không đổi)
    
    # 10. Sync back
    # sync_from_tensors(snn_ctx)  # ← XÓA dòng này
```

**Sync chỉ khi cần**:
- `process_periodic_resync` (đã có trong workflow, line 35)
- Checkpoint save (tự động)
- Dashboard visualization (nếu có)

### Ưu điểm

| Tiêu chí | Đánh giá |
|----------|----------|
| **Tốc độ** | ⭐⭐⭐⭐⭐ (15-20x faster) |
| **Đơn giản** | ⭐⭐⭐⭐⭐ (Xóa 1 dòng) |
| **Đúng đắn** | ⭐⭐⭐⭐⭐ (Tensors = Source of Truth) |

**Lý do nhanh hơn**:
- Giảm từ 11,000 syncs → ~110 syncs (mỗi episode 1 lần qua `periodic_resync`)
- **100x ít object updates hơn**

**Triết lý**:
- Tensors là **cache tính toán** (nhanh)
- Objects là **persistence layer** (chậm nhưng cần cho checkpoint)
- Chỉ sync khi **cần lưu trữ hoặc hiển thị**

### Nhược điểm

| Rủi ro | Mức độ | Giải pháp |
|--------|--------|-----------|
| **Debug khó hơn** | Thấp | Objects không real-time, nhưng tensors vẫn đúng |
| **Checkpoint sai** | Không có | `periodic_resync` đảm bảo sync trước checkpoint |
| **Dashboard lag** | Thấp | Nếu có dashboard, thêm sync vào visualization hook |

---

## Option 2: Conditional Sync (Sync mỗi N steps)

### Thay đổi

```python
# src/processes/snn_homeostasis_theus.py
def process_homeostasis(ctx: SNNSystemContext):
    # ... (logic không đổi)
    
    # 10. Sync back (Conditional)
    if snn_domain.current_time % 10 == 0:  # Mỗi 10 timesteps
        sync_from_tensors(snn_ctx)
```

### Ưu điểm

| Tiêu chí | Đánh giá |
|----------|----------|
| **Tốc độ** | ⭐⭐⭐⭐ (10x faster) |
| **Đơn giản** | ⭐⭐⭐⭐ (Thêm 1 dòng if) |
| **Debug dễ** | ⭐⭐⭐⭐ (Objects gần real-time) |

**Lý do nhanh hơn**:
- Giảm từ 11,000 syncs → 1,100 syncs (10% của cũ)
- **10x ít object updates hơn**

**Trade-off linh hoạt**:
- `N = 5`: 5x faster, objects lag 5 steps
- `N = 10`: 10x faster, objects lag 10 steps
- `N = 50`: 50x faster, objects lag 50 steps

### Nhược điểm

| Rủi ro | Mức độ | Giải pháp |
|--------|--------|-----------|
| **Vẫn chậm hơn Option 1** | Trung bình | Chấp nhận trade-off |
| **Objects không sync** | Thấp | Lag tối đa N steps, chấp nhận được |
| **Magic number N** | Thấp | Cần tuning, nhưng N=10 là hợp lý |

---

## So sánh trực tiếp

| Tiêu chí | Option 1: Lazy Sync | Option 2: Conditional (N=10) |
|----------|---------------------|------------------------------|
| **Tốc độ** | 15-20x faster | 10x faster |
| **Syncs/experiment** | ~110 | ~1,100 |
| **Object lag** | Đến khi `periodic_resync` | Tối đa 10 steps |
| **Code complexity** | Xóa 1 dòng | Thêm 1 dòng if |
| **Rủi ro** | Rất thấp | Thấp |
| **Khuyến nghị** | ✅ **Tốt nhất** | ⚠️ Backup nếu cần debug |

---

## Khuyến nghị cuối cùng

### Chọn Option 1 nếu:
- ✅ Ưu tiên **tốc độ tối đa**
- ✅ Tin tưởng vào **Compute-Sync architecture** của Theus
- ✅ Không cần debug objects real-time

### Chọn Option 2 nếu:
- ⚠️ Cần **debug objects** thường xuyên
- ⚠️ Lo ngại về **correctness** (mặc dù không cần thiết)
- ⚠️ Muốn **thay đổi ít nhất** (conservative)

---

## Kết luận

**Option 1 (Lazy Sync)** là lựa chọn tốt hơn vì:
1. **Nhanh hơn** (15-20x vs 10x)
2. **Đơn giản hơn** (xóa vs thêm logic)
3. **Đúng với thiết kế** (Tensors = Source of Truth trong compute phase)
4. **Không rủi ro** (`periodic_resync` đảm bảo checkpoint đúng)

Nếu sau này cần debug, có thể tạm thời enable sync lại hoặc dùng Option 2 với N nhỏ (N=5).
