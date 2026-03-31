"""Quick Darwinism v2 Metrics Analyzer — Only last N lines."""
import json, sys

METRICS_FILE = "results/Optimization_Sanity_Check/metrics.jsonl"
TAIL_N = 30  # Last 30 episodes

# Read only tail
with open(METRICS_FILE, 'rb') as f:
    # Seek near end
    f.seek(0, 2)
    fsize = f.tell()
    # Read last 200KB max
    read_size = min(fsize, 200_000)
    f.seek(fsize - read_size)
    tail_bytes = f.read()

lines = tail_bytes.decode('utf-8', errors='ignore').strip().split('\n')
# Take last N valid JSON
records = []
for line in lines[-TAIL_N:]:
    line = line.strip()
    if not line:
        continue
    try:
        records.append(json.loads(line))
    except json.JSONDecodeError:
        pass

print("=" * 90)
print("DARWINISM v2 (Monotonic Additive Plasticity) — METRICS REPORT")
print("=" * 90)
print(f"{'Ep':>5} | {'Synapses':>8} | {'GC':>4} | {'New':>4} | {'Skull%':>7} | {'Loss':>10} | {'Reward':>8} | {'FR':>8}")
print("-" * 90)

for d in records:
    ep = d.get('episode', '?')
    syn = d.get('darwinism_total_synapses', d.get('debug_total_synapses', 'N/A'))
    gc = d.get('darwinism_gc_count', 'N/A')
    new_s = d.get('darwinism_new_synapses', 'N/A')
    skull = d.get('darwinism_skull_usage_pct', 'N/A')
    loss = d.get('neural_loss', 'N/A')
    reward = d.get('reward', 'N/A')
    fr = d.get('fire_rate', 'N/A')
    
    loss_str = f"{loss:.4f}" if isinstance(loss, (int, float)) else str(loss)
    reward_str = f"{reward:.2f}" if isinstance(reward, (int, float)) else str(reward)
    fr_str = f"{fr:.4f}" if isinstance(fr, (int, float)) else str(fr)
    
    print(f"{str(ep):>5} | {str(syn):>8} | {str(gc):>4} | {str(new_s):>4} | {str(skull):>7} | {loss_str:>10} | {reward_str:>8} | {fr_str:>8}")

# Summary
if records:
    synapse_counts = [d.get('darwinism_total_synapses', d.get('debug_total_synapses')) for d in records if d.get('darwinism_total_synapses') or d.get('debug_total_synapses')]
    gc_counts = [d.get('darwinism_gc_count', 0) for d in records if d.get('darwinism_gc_count') is not None]
    new_counts = [d.get('darwinism_new_synapses', 0) for d in records if d.get('darwinism_new_synapses') is not None]
    losses = [d.get('neural_loss') for d in records if isinstance(d.get('neural_loss'), (int, float))]
    rewards = [d.get('reward') for d in records if isinstance(d.get('reward'), (int, float))]
    
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    if synapse_counts:
        valid = [x for x in synapse_counts if x is not None]
        if valid:
            print(f"  Synapses: {valid[0]} (first) -> {valid[-1]} (last) | Change: {valid[-1] - valid[0]:+d}")
    if gc_counts:
        print(f"  Silent GC total: {sum(gc_counts)} synapses removed")
    if new_counts:
        print(f"  Synaptogenesis total: {sum(new_counts)} new synapses grown")
    if losses:
        print(f"  Loss: min={min(losses):.4f} max={max(losses):.4f} avg={sum(losses)/len(losses):.4f}")
        spike_count = sum(1 for l in losses if l > 1000)
        print(f"  Loss Spikes (>1000): {spike_count}")
    if rewards:
        print(f"  Reward: min={min(rewards):.2f} max={max(rewards):.2f} avg={sum(rewards)/len(rewards):.2f}")
