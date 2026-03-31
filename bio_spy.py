"""
SNN Bio-spy v2: Đo lường hiệu suất Monotonic Additive Plasticity
Đọc metrics.jsonl bằng cách seek tail, không load toàn bộ file.
"""
import json, sys, os

METRICS_FILE = "results/multi_agent_complex_maze/metrics.jsonl"

# === Đọc tail hiệu quả ===
with open(METRICS_FILE, 'rb') as f:
    f.seek(0, 2)
    fsize = f.tell()
    read_size = min(fsize, 100_000)  # 100KB cuối
    f.seek(fsize - read_size)
    tail = f.read().decode('utf-8', errors='ignore')

lines = tail.strip().split('\n')

# Tách run cũ và run mới (episode resets)
all_records = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    try:
        all_records.append(json.loads(line))
    except json.JSONDecodeError:
        pass

# Tìm điểm bắt đầu run mới (episode 0 xuất hiện lại)
run_start = 0
for i, r in enumerate(all_records):
    ep = r.get('episode', -1)
    if ep == 0 and i > 0:
        run_start = i  # Run mới nhất

records = all_records[run_start:]

print("=" * 90)
print("🧬 SNN BIO-SPY v2 — Monotonic Additive Plasticity Health Check")
print("=" * 90)

# === 1. Synapse Population ===
print("\n📊 1. SYNAPSE POPULATION (from debug_total_synapses)")
print("-" * 60)
syn_data = []
for r in records:
    m = r.get('metrics', r)
    ep = r.get('episode', m.get('episode', '?'))
    syn = m.get('debug_total_synapses', None)
    if syn is not None:
        syn_data.append((ep, syn))
        
if syn_data:
    for ep, syn in syn_data:
        bar = '█' * max(1, syn // 200)
        print(f"  Ep {ep:>4}: {syn:>6} synapses {bar}")
    
    first_s = syn_data[0][1]
    last_s = syn_data[-1][1]
    delta = last_s - first_s
    print(f"\n  Δ Synapses: {first_s} → {last_s} ({delta:+d})")
    
    # Check monotonic growth (hoặc mild decrease từ Silent GC)
    drops = 0
    for i in range(1, len(syn_data)):
        if syn_data[i][1] < syn_data[i-1][1]:
            drops += 1
    if drops == 0:
        print("  ✅ Hoàn toàn Monotonic (tăng đơn điệu) — Không có cú sốc xóa!")
    else:
        print(f"  ⚠️ {drops} lần giảm (có thể từ Silent GC — kiểm tra mức giảm)")

# === 2. MLP Health ===
print("\n📊 2. MLP HEALTH (Loss & Gradient Stability)")
print("-" * 60)
losses = []
for r in records:
    m = r.get('metrics', r)
    loss = m.get('neural_loss_avg', m.get('neural_loss'))
    if isinstance(loss, (int, float)):
        losses.append(loss)

if losses:
    spikes = [l for l in losses if l > 1000]
    print(f"  Loss range: {min(losses):.4f} — {max(losses):.4f}")
    print(f"  Loss avg: {sum(losses)/len(losses):.4f}")
    print(f"  Loss spikes (>1000): {len(spikes)}")
    if len(spikes) == 0:
        print("  ✅ Không có Gradient Explosion — MLP Input ổn định!")
    else:
        print("  ❌ CÓ gradient explosion — cần điều tra!")

# === 3. Reward Trend ===
print("\n📊 3. REWARD TREND")
print("-" * 60)
rewards = []
for r in records:
    m = r.get('metrics', r)
    reward = m.get('avg_reward', m.get('reward'))
    if isinstance(reward, (int, float)):
        rewards.append(reward)

if rewards:
    n = len(rewards)
    first_half = rewards[:n//2]
    second_half = rewards[n//2:]
    
    avg_first = sum(first_half) / max(len(first_half), 1)
    avg_second = sum(second_half) / max(len(second_half), 1)
    
    print(f"  First half avg: {avg_first:.2f}")
    print(f"  Second half avg: {avg_second:.2f}")
    print(f"  Improvement: {avg_second - avg_first:+.2f}")
    
    if avg_second > avg_first:
        print("  ✅ Reward đang cải thiện — Agent đang học!")
    else:
        print("  ⚠️ Reward không cải thiện — có thể cần thêm episodes")

# === 4. Firing Rate ===
print("\n📊 4. FIRING RATE STABILITY")  
print("-" * 60)
fire_rates = []
for r in records:
    m = r.get('metrics', r)
    fr = m.get('avg_firing_rate', m.get('fire_rate'))
    if isinstance(fr, (int, float)):
        fire_rates.append(fr)

if fire_rates:
    import statistics
    std = statistics.stdev(fire_rates) if len(fire_rates) > 1 else 0
    print(f"  Range: {min(fire_rates):.4f} — {max(fire_rates):.4f}")
    print(f"  Avg: {sum(fire_rates)/len(fire_rates):.4f}")
    print(f"  Std: {std:.4f}")
    if std < 0.1:
        print("  ✅ Firing rate ổn định — SNN Homeostasis hoạt động tốt!")
    else:
        print("  ⚠️ Firing rate biến động — Homeostasis có thể cần tune")

# === 5. Skull Limit ===
print("\n📊 5. SKULL LIMIT CHECK")
print("-" * 60)
if syn_data:
    last_syn = syn_data[-1][1]
    # N=1024 neurons (from multi_agent_complex_maze config)
    N = 1024
    max_limit = int(N * (N - 1) * 0.3)
    usage_pct = last_syn / max(max_limit, 1) * 100
    print(f"  Current synapses: {last_syn}")
    print(f"  Dynamic Skull Limit (N={N}): {max_limit}")
    print(f"  Usage: {usage_pct:.1f}%")
    if usage_pct < 90:
        print("  ✅ Còn dung lượng mọc rễ mới")
    else:
        print("  ⚠️ Sọ não gần đầy — Synaptogenesis sẽ dừng")

# === 6. Success Rate ===  
print("\n📊 6. SUCCESS RATE")
print("-" * 60)
successes = 0
total = 0
for r in records:
    m = r.get('metrics', r)
    sr = m.get('success_rate')
    if isinstance(sr, (int, float)):
        successes += sr
        total += 1
if total > 0:
    print(f"  Average success rate: {successes/total*100:.1f}%")

print("\n" + "=" * 90)
print("BIO-SPY COMPLETE")
print("=" * 90)
