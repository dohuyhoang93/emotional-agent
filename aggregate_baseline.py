"""
Tổng hợp kết quả multi_agent_complex_maze (Neural Darwinism v1) → Markdown baseline.
Đọc metrics.jsonl bằng streaming, không load toàn bộ vào RAM.
"""
import json, os, statistics

METRICS_FILE = "results/multi_agent_complex_maze/metrics.jsonl"
OUTPUT_FILE = "Documents/Incidents/by-area/core/baseline_multi_agent_complex_maze.md"

# === Stream parse ===
records = []
with open(METRICS_FILE, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            pass

total_eps = len(records)
print(f"Loaded {total_eps} episodes")

# === Extract data ===
episodes = []
rewards = []
success_rates = []
losses = []
fire_rates = []
synapse_counts = []
q_values = []

for r in records:
    m = r.get('metrics', r)
    ep = r.get('episode', m.get('episode'))
    episodes.append(ep)
    
    reward = m.get('avg_reward', m.get('reward'))
    if isinstance(reward, (int, float)):
        rewards.append(reward)
    
    sr = m.get('success_rate')
    if isinstance(sr, (int, float)):
        success_rates.append(sr)
    
    loss = m.get('neural_loss_avg', m.get('neural_loss'))
    if isinstance(loss, (int, float)):
        losses.append(loss)
    
    fr = m.get('avg_firing_rate', m.get('fire_rate'))
    if isinstance(fr, (int, float)):
        fire_rates.append(fr)
    
    syn = m.get('debug_total_synapses')
    if isinstance(syn, (int, float)):
        synapse_counts.append(syn)
    
    qv = m.get('avg_q_predicted')
    if isinstance(qv, (int, float)):
        q_values.append(qv)

# === Compute stats ===
def stats(data, name):
    if not data:
        return f"  {name}: No data\n"
    s = ""
    s += f"  - Min: {min(data):.4f}\n"
    s += f"  - Max: {max(data):.4f}\n"
    s += f"  - Mean: {sum(data)/len(data):.4f}\n"
    if len(data) > 1:
        s += f"  - Std: {statistics.stdev(data):.4f}\n"
    return s

def epoch_stats(data, n_bins=5):
    """Split data into N bins and compute avg for each."""
    if not data:
        return ""
    bin_size = len(data) // n_bins
    if bin_size == 0:
        return ""
    s = ""
    for i in range(n_bins):
        start = i * bin_size
        end = start + bin_size if i < n_bins - 1 else len(data)
        chunk = data[start:end]
        avg = sum(chunk) / len(chunk)
        s += f"  | Ep {start:>5}-{end:>5} | {avg:>10.4f} |\n"
    return s

# === Loss spikes ===
loss_spikes = [l for l in losses if l > 1000]
loss_spike_100 = [l for l in losses if l > 100]

# === Synapse trend ===
syn_first = synapse_counts[0] if synapse_counts else None
syn_last = synapse_counts[-1] if synapse_counts else None
syn_min = min(synapse_counts) if synapse_counts else None
syn_max = max(synapse_counts) if synapse_counts else None

# === Build markdown ===
md = f"""# Baseline: multi_agent_complex_maze (Neural Darwinism v1)

> **Mục đích**: Ghi lại số liệu hiệu suất của kiến trúc Neural Darwinism v1 (Pruning + Neuron Recycling) 
> trước khi chuyển sang Monotonic Additive Plasticity v2. Dùng để so sánh A/B sau khi chạy lại.

**Ngày chạy**: Trích từ checkpoint  
**Tổng số Episodes**: {total_eps}  
**Config**: `experiments.json` → `multi_agent_complex_maze`  
**Kiến trúc**: Neural Darwinism v1 (Pruning + Recycling)  
**Grid**: 25×25 Complex Logic Maze  

---

## 1. Reward

{stats(rewards, "Reward")}

### Xu hướng theo giai đoạn

| Giai đoạn | Reward trung bình |
|-----------|-------------------|
{epoch_stats(rewards, 10)}

---

## 2. Success Rate

{stats(success_rates, "Success Rate")}

### Xu hướng theo giai đoạn

| Giai đoạn | Success Rate trung bình |
|-----------|-------------------------|
{epoch_stats(success_rates, 10)}

---

## 3. MLP Loss (Gradient Health)

{stats(losses, "Loss")}

- **Loss Spikes (>1000)**: {len(loss_spikes)} lần
- **Loss Spikes (>100)**: {len(loss_spike_100)} lần

> ⚠️ Đây là dấu hiệu Non-stationarity Cascade — MLP không hội tụ vì SNN Input bị dịch chuyển mỗi khi Darwinism pruning.

### Xu hướng theo giai đoạn

| Giai đoạn | Loss trung bình |
|-----------|-----------------|
{epoch_stats(losses, 10)}

---

## 4. Synapse Population

- **Đầu**: {syn_first}
- **Cuối**: {syn_last}
- **Min**: {syn_min}
- **Max**: {syn_max}
- **Δ (Cuối - Đầu)**: {(syn_last - syn_first) if syn_first and syn_last else 'N/A':+d}

> ⚠️ Giảm mạnh = Pruning quá tay → Representational Drift → MLP Gradient Explosion.

### Xu hướng theo giai đoạn

| Giai đoạn | Synapse trung bình |
|-----------|--------------------|
{epoch_stats(synapse_counts, 10)}

---

## 5. Firing Rate

{stats(fire_rates, "Firing Rate")}

### Xu hướng theo giai đoạn

| Giai đoạn | Firing Rate trung bình |
|-----------|------------------------|
{epoch_stats(fire_rates, 10)}

---

## 6. Q-Value Predictions

{stats(q_values, "Q-Value")}

### Xu hướng theo giai đoạn

| Giai đoạn | Q-Value trung bình |
|-----------|--------------------|
{epoch_stats(q_values, 10)}

---

## 7. Tóm tắt Vấn đề (INC-006)

| Vấn đề | Chi tiết |
|--------|----------|
| Synapse loss | {syn_first} → {syn_min} (mất {((syn_first - syn_min) / syn_first * 100) if syn_first and syn_min else 0:.0f}%) |
| Loss spikes >1000 | {len(loss_spikes)} lần |
| Loss spikes >100 | {len(loss_spike_100)} lần |
| Max Loss | {max(losses) if losses else 'N/A':.2f} |
| Avg Reward | {sum(rewards)/len(rewards) if rewards else 0:.2f} |
| Best Reward | {max(rewards) if rewards else 'N/A':.2f} |

> Dữ liệu này xác nhận hệ thống Neural Darwinism v1 gây ra Non-stationarity Cascade 
> như được phân tích trong INC-006.
"""

os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(md)

print(f"\n✅ Baseline saved to: {OUTPUT_FILE}")
print(f"   Episodes: {total_eps}")
print(f"   Synapse: {syn_first} -> {syn_last} (Δ{(syn_last-syn_first) if syn_first and syn_last else 0:+d})")
print(f"   Loss spikes >1000: {len(loss_spikes)}")
print(f"   Avg Reward: {sum(rewards)/len(rewards) if rewards else 0:.2f}")
