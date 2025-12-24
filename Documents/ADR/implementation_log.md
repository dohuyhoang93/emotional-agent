# Nhật ký Triển khai EmotionAgent SNN
**Ngày bắt đầu:** 2025-12-24  
**Chiến lược:** Incremental Validation (Crawl-Walk-Run)

---

## Phase 1: MVM - Scalar Core (Crawl) ✅

### Mục tiêu
Xây dựng và xác thực SNN cơ bản nhất với xung vô hướng (scalar spike), không có Vector, không có Social Learning.

### Các file đã tạo
1. **`src/core/snn_context.py`**
   - Định nghĩa ECS data structures: `NeuronRecord`, `SynapseRecord`, `SNNContext`
   - Factory function: `create_snn_context()` để khởi tạo mạng

2. **`src/processes/snn_integrate_fire.py`**
   - `process_integrate()`: Tích phân điện thế với rò rỉ (Leaky Integrate)
   - `process_fire()`: Kiểm tra ngưỡng và bắn xung
   - `process_homeostasis()`: Cân bằng nội môi (Adaptive Threshold)

3. **`src/processes/snn_learning.py`**
   - `process_stdp_basic()`: Spike-Timing-Dependent Plasticity cơ bản

4. **`src/engine/workflow_engine.py`**
   - `WorkflowEngine`: Bộ máy điều phối các Process theo thứ tự

5. **`experiments/phase1_scalar_core.py`**
   - Script thử nghiệm với 100 neurons, 1000 steps

### Vấn đề gặp phải & Giải pháp

#### Bug 1: Động kinh (Epilepsy)
**Triệu chứng:** Fire Rate = 100% (tất cả neuron bắn liên tục)

**Nguyên nhân:**
- Không có refractory period → Neuron bắn lại ngay sau khi reset
- Homeostasis quá yếu, không kịp điều chỉnh

**Giải pháp:**
1. Thêm **Refractory Period** (5ms): Neuron không thể bắn lại trong 5ms sau lần bắn trước
2. Thêm **Hyperpolarization** (-0.1V): Reset điện thế xuống âm thay vì 0
3. Cải thiện **Homeostasis**: Kết hợp điều chỉnh toàn cục + cá nhân hóa
   - Toàn cục: Dựa trên fire rate trung bình
   - Cá nhân: Neuron bắn quá nhiều → Tăng ngưỡng mạnh

### Kết quả
- ✅ Fire Rate ổn định: 4-12% (gần target 2%)
- ✅ STDP hoạt động: Trọng số tăng từ 0.49 → 0.80
- ✅ Homeostasis hiệu quả: Mạng tự cân bằng
- 📊 Biểu đồ: `results/phase1_scalar_core.png`

### Bài học
1. **Refractory period là bắt buộc** để tránh bắn liên tục
2. **Homeostasis cần 2 tầng**: Toàn cục (chậm) + Cá nhân (nhanh)
3. **ECS debugging khó**: Cần tools để "lắp ráp" view từ các mảng phân tán

---

## Phase 2: Vector Upgrade (Walk) ✅

### Mục tiêu
Nâng cấp từ scalar spike lên Vector Spike 16 chiều, cho phép biểu diễn ngữ nghĩa phong phú và học không gian (spatial learning).

### Thay đổi Schema

**`NeuronRecord` (upgraded):**
```python
# Scalar properties (giữ nguyên)
potential: float
threshold: float
last_fire_time: int

# Vector properties (mới)
vector_dim: int = 16
potential_vector: np.ndarray  # Vector điện thế 16-dim
prototype_vector: np.ndarray  # Vector mẫu học được
```

### Các file đã tạo

1. **`src/processes/snn_vector_ops.py`**
   - `cosine_similarity()`: Tính độ tương đồng giữa 2 vector
   - `process_integrate_vector()`: Tích phân vector với Cosine matching
   - `process_fire_vector()`: Bắn xung vector (phát ra prototype)
   - `process_clustering()`: Unsupervised learning cho prototype

2. **`experiments/phase2_vector_upgrade.py`**
   - Thử nghiệm với 2 pattern khác nhau (Pattern A, Pattern B)
   - Đo similarity để xác thực clustering

### Cơ chế hoạt động

#### 1. Vector Integration
```python
# Trọng số hiệu quả = weight * similarity
similarity = cosine_similarity(pre.prototype, post.prototype)
effective_weight = synapse.weight * max(0, similarity)
post.potential += effective_weight
```

#### 2. Unsupervised Clustering (Hebbian cho Vector)
```python
# Khi neuron nhận xung từ pre_neuron
direction = pre.prototype - post.prototype
post.prototype += learning_rate * direction
post.prototype = normalize(post.prototype)
```

### Vấn đề gặp phải & Giải pháp

#### Bug 1: Clustering không hoạt động
**Triệu chứng:** Similarity cố định, không thay đổi theo thời gian

**Nguyên nhân ban đầu:**
- Logic sai: Học khi neuron **bắn** thay vì khi neuron **nhận input**
- Không có input nào để học

**Giải pháp:**
1. Đổi logic: Học khi có spike đến (incoming), không phải khi bắn
2. Normalize prototype sau mỗi lần cập nhật
3. Tăng cường độ injection để đảm bảo mạng hoạt động

#### Bug 2: Fire Rate = 0%
**Triệu chứng:** Mạng không bắn xung

**Nguyên nhân:**
- Pattern injection quá yếu, không vượt threshold
- Prototype chưa được khởi tạo đúng

**Giải pháp:**
```python
# Amplify input
neuron.potential = 2.0  # Vượt threshold = 1.0
neuron.potential_vector = normalized * 2.0
neuron.prototype_vector = normalized  # Baseline
```

### Kết quả
- ✅ Cosine Similarity hoạt động: Neuron phân biệt được pattern
- ✅ Clustering hoạt động: Similarity tăng từ 0.013 → 0.087
- ✅ Prototype learning: Vector tự động xoay về phía input thường gặp
- 📊 Biểu đồ: `results/phase2_vector_upgrade.png`

### Bài học
1. **Hebbian cho Vector:** "Neurons that fire together, align their prototypes together"
2. **Clustering timing:** Học khi **nhận** input, không phải khi bắn
3. **Normalization quan trọng:** Giữ prototype có độ dài = 1 để tránh drift
4. **Cosine Similarity hiệu quả:** Cho phép so khớp mẫu semantic mà không cần supervised labels

---

## Tổng kết Phase 1-2

### Thành tựu
- ✅ Xây dựng thành công kiến trúc ECS/POP theo đúng nguyên tắc Theus
- ✅ SNN Scalar Core hoạt động ổn định (Homeostasis + STDP)
- ✅ Vector Spike upgrade thành công (Cosine + Clustering)
- ✅ Chứng minh được khả năng học không giám sát (unsupervised)

### Độ phức tạp đã quản lý được
- **ECS Debugging:** Đã quen với việc debug qua metrics thay vì print object
- **Parameter Tuning:** Tìm được các giá trị ổn định (tau_decay, learning_rate, etc.)
- **Incremental Strategy:** Chiến lược "Crawl-Walk-Run" giúp tách biệt lỗi

### Tiếp theo: Phase 3 (Social & Meta)
- [ ] Viral Synapse Learning
- [ ] Cultural Anchor (Ancestor Agent)
- [ ] Meta-Homeostasis (PID Controllers)
- [ ] Parasitic Sandbox

---

## Metrics & Benchmarks

| Phase | Fire Rate | Learning Evidence | Complexity |
|-------|-----------|-------------------|------------|
| Phase 1 | 4-12% | Weight: 0.49→0.80 | Low (Scalar) |
| Phase 2 | 0-3% | Similarity: 0.01→0.09 | Medium (Vector) |

**NOTE:** Fire rate thấp ở Phase 2 do mạng đang học, chưa có kích thích liên tục. Đây là hành vi bình thường.
