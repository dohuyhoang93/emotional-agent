import json
import numpy as np

def load_metrics(filepath):
    metrics = []
    with open(filepath, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    metrics.append(data)
                except:
                    pass
    return metrics

def get_learning_curve(metrics, bin_size=500):
    if not metrics:
        return []
    
    curve = []
    for i in range(0, len(metrics), bin_size):
        chunk = metrics[i:i+bin_size]
        avg_reward = np.mean([m['metrics'].get('avg_reward', 0) for m in chunk])
        success = np.mean([m['metrics'].get('success_rate', 0) for m in chunk])
        curve.append((i, i+bin_size, avg_reward, success))
    return curve

old_path = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_DeepRL\metrics.jsonl'
new_path = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_DeepRL_Path_Darwinism\metrics.jsonl'

old_m = load_metrics(old_path)
new_m = load_metrics(new_path)

c_old = get_learning_curve(old_m)
c_new = get_learning_curve(new_m)

print(f"{'Episodes':<15} | {'Old Reward':<12} | {'New Reward':<12} | {'Old Success':<12} | {'New Success':<12}")
print("-" * 75)
for i in range(min(len(c_old), len(c_new))):
    e_range = f"{c_old[i][0]}-{c_old[i][1]}"
    print(f"{e_range:<15} | {c_old[i][2]:<12.3f} | {c_new[i][2]:<12.3f} | {c_old[i][3]:<12.3f} | {c_new[i][3]:<12.3f}")

