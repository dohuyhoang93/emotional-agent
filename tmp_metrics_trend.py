import json
import statistics

filepath = r'C:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl'
lines = []
with open(filepath, 'r') as f:
    for line in f:
        if line.strip():
            lines.append(json.loads(line))

if len(lines) < 100:
    print("Not enough episodes to split into 50/50")
    first_half = lines[:len(lines)//2]
    last_half = lines[len(lines)//2:]
else:
    first_50 = lines[:50]
    last_50 = lines[-50:]

def get_avg(data, key):
    vals = [x['metrics'].get(key) for x in data if key in x['metrics'] and x['metrics'][key] is not None]
    if not vals: return None
    return sum(vals)/len(vals)

keys = ['avg_reward', 'success_rate', 'epsilon', 'maturity', 'avg_firing_rate', 'debug_total_synapses', 'neural_loss_avg', 'avg_q_predicted', 'debug_process_memory_mb']

print("=== FIRST 50 EPISODES ===")
for k in keys:
    print(f"{k}: {get_avg(first_50, k):.4f}")

print("\n=== LAST 50 EPISODES ===")
for k in keys:
    print(f"{k}: {get_avg(last_50, k):.4f}")

print("\n=== MAX REWARD EPISODE ===")
max_reward_idx = max(range(len(lines)), key=lambda i: lines[i]['metrics'].get('avg_reward', -999))
print(f"Episode: {lines[max_reward_idx]['episode']}")
for k in keys:
    print(f"{k}: {lines[max_reward_idx]['metrics'].get(k)}")
