# Baseline: multi_agent_complex_maze (Neural Darwinism v1)

> **Mục đích**: Ghi lại số liệu hiệu suất của kiến trúc Neural Darwinism v1 (Pruning + Neuron Recycling) 
> trước khi chuyển sang Monotonic Additive Plasticity v2. Dùng để so sánh A/B sau khi chạy lại.

**Ngày chạy**: Trích từ checkpoint  
**Tổng số Episodes**: 5000  
**Config**: `experiments.json` → `multi_agent_complex_maze`  
**Kiến trúc**: Neural Darwinism v1 (Pruning + Recycling)  
**Grid**: 25×25 Complex Logic Maze  

---

## 1. Reward

  - Min: -225.2711
  - Max: 618.0737
  - Mean: -178.5059
  - Std: 47.1284


### Xu hướng theo giai đoạn

| Giai đoạn | Reward trung bình |
|-----------|-------------------|
  | Ep     0-  500 |   -83.7897 |
  | Ep   500- 1000 |  -120.9948 |
  | Ep  1000- 1500 |  -152.4264 |
  | Ep  1500- 2000 |  -175.0326 |
  | Ep  2000- 2500 |  -193.2863 |
  | Ep  2500- 3000 |  -209.1085 |
  | Ep  3000- 3500 |  -212.9907 |
  | Ep  3500- 4000 |  -211.3217 |
  | Ep  4000- 4500 |  -212.9981 |
  | Ep  4500- 5000 |  -213.1101 |


---

## 2. Success Rate

  - Min: 0.0000
  - Max: 1.0000
  - Mean: 0.0188
  - Std: 0.1358


### Xu hướng theo giai đoạn

| Giai đoạn | Success Rate trung bình |
|-----------|-------------------------|
  | Ep     0-  500 |     0.0220 |
  | Ep   500- 1000 |     0.0300 |
  | Ep  1000- 1500 |     0.0200 |
  | Ep  1500- 2000 |     0.0300 |
  | Ep  2000- 2500 |     0.0380 |
  | Ep  2500- 3000 |     0.0080 |
  | Ep  3000- 3500 |     0.0040 |
  | Ep  3500- 4000 |     0.0120 |
  | Ep  4000- 4500 |     0.0160 |
  | Ep  4500- 5000 |     0.0080 |


---

## 3. MLP Loss (Gradient Health)

  - Min: 0.0000
  - Max: 2403.4858
  - Mean: 2.0568
  - Std: 39.4873


- **Loss Spikes (>1000)**: 2 lần
- **Loss Spikes (>100)**: 2 lần

> ⚠️ Đây là dấu hiệu Non-stationarity Cascade — MLP không hội tụ vì SNN Input bị dịch chuyển mỗi khi Darwinism pruning.

### Xu hướng theo giai đoạn

| Giai đoạn | Loss trung bình |
|-----------|-----------------|
  | Ep     0-  500 |     8.8870 |
  | Ep   500- 1000 |     2.0492 |
  | Ep  1000- 1500 |     1.3997 |
  | Ep  1500- 2000 |     2.1015 |
  | Ep  2000- 2500 |     2.6659 |
  | Ep  2500- 3000 |     0.5798 |
  | Ep  3000- 3500 |     0.3029 |
  | Ep  3500- 4000 |     0.8597 |
  | Ep  4000- 4500 |     1.1436 |
  | Ep  4500- 5000 |     0.5791 |


---

## 4. Synapse Population

- **Đầu**: 26873
- **Cuối**: 4940
- **Min**: 3437
- **Max**: 26873
- **Δ (Cuối - Đầu)**: -21933

> ⚠️ Giảm mạnh = Pruning quá tay → Representational Drift → MLP Gradient Explosion.

### Xu hướng theo giai đoạn

| Giai đoạn | Synapse trung bình |
|-----------|--------------------|
  | Ep     0-  500 | 13644.4500 |
  | Ep   500- 1000 | 13402.5740 |
  | Ep  1000- 1500 | 13844.8440 |
  | Ep  1500- 2000 | 13685.9840 |
  | Ep  2000- 2500 | 11575.7120 |
  | Ep  2500- 3000 |  6815.5840 |
  | Ep  3000- 3500 |  5744.6980 |
  | Ep  3500- 4000 |  5195.6120 |
  | Ep  4000- 4500 |  5529.6060 |
  | Ep  4500- 5000 |  5092.1560 |


---

## 5. Firing Rate

  - Min: 0.0713
  - Max: 0.1631
  - Mean: 0.1102
  - Std: 0.0248


### Xu hướng theo giai đoạn

| Giai đoạn | Firing Rate trung bình |
|-----------|------------------------|
  | Ep     0-  500 |     0.1343 |
  | Ep   500- 1000 |     0.1352 |
  | Ep  1000- 1500 |     0.1385 |
  | Ep  1500- 2000 |     0.1363 |
  | Ep  2000- 2500 |     0.1239 |
  | Ep  2500- 3000 |     0.0978 |
  | Ep  3000- 3500 |     0.0847 |
  | Ep  3500- 4000 |     0.0825 |
  | Ep  4000- 4500 |     0.0866 |
  | Ep  4500- 5000 |     0.0824 |


---

## 6. Q-Value Predictions

  - Min: -8.6154
  - Max: 1787.4529
  - Mean: -6.4591
  - Std: 26.2097


### Xu hướng theo giai đoạn

| Giai đoạn | Q-Value trung bình |
|-----------|--------------------|
  | Ep     0-  500 |     3.0856 |
  | Ep   500- 1000 |    -4.6313 |
  | Ep  1000- 1500 |    -5.9805 |
  | Ep  1500- 2000 |    -6.9718 |
  | Ep  2000- 2500 |    -7.7462 |
  | Ep  2500- 3000 |    -8.3287 |
  | Ep  3000- 3500 |    -8.5096 |
  | Ep  3500- 4000 |    -8.4529 |
  | Ep  4000- 4500 |    -8.5359 |
  | Ep  4500- 5000 |    -8.5198 |


---

## 7. Tóm tắt Vấn đề (INC-006)

| Vấn đề | Chi tiết |
|--------|----------|
| Synapse loss | 26873 → 3437 (mất 87%) |
| Loss spikes >1000 | 2 lần |
| Loss spikes >100 | 2 lần |
| Max Loss | 2403.49 |
| Avg Reward | -178.51 |
| Best Reward | 618.07 |

> Dữ liệu này xác nhận hệ thống Neural Darwinism v1 gây ra Non-stationarity Cascade 
> như được phân tích trong INC-006.
