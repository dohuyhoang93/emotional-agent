import json
import numpy as np

def load_metrics(filepath):
    metrics = []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        metrics.append(data)
                    except:
                        pass
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return metrics

def get_learning_curve(metrics, bin_size=500):
    if not metrics:
        return []
    
    curve = []
    for i in range(0, len(metrics), bin_size):
        chunk = metrics[i:i+bin_size]
        avg_reward = np.mean([m['metrics'].get('avg_reward', 0) for m in chunk])
        success = np.mean([m['metrics'].get('success_rate', 0) for m in chunk])
        curve.append((i, i+len(chunk), avg_reward, success))
    return curve

def get_summary(metrics):
    if not metrics:
        return {}
    recent = metrics[-500:]
    avg_reward = np.mean([m['metrics'].get('avg_reward', 0) for m in recent])
    success = np.mean([m['metrics'].get('success_rate', 0) for m in recent])
    return {'avg_r': avg_reward, 'success': success}

path_snnrl = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_Check\metrics.jsonl'
path_new = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_DeepRL_Path_Darwinism\metrics.jsonl'

m_snnrl = load_metrics(path_snnrl)
m_new = load_metrics(path_new)

c_snnrl = get_learning_curve(m_snnrl)
c_new = get_learning_curve(m_new)

print("Original SNN-RL: Episodes:", len(m_snnrl))
print("Original SNN-RL Summary (last 500):", get_summary(m_snnrl))
print("Reward-Based Darwinism (DeepRL) Summary (last 500):", get_summary(m_new))

print("\nLearning Curve:")
print(f"{'Episodes':<15} | {'SNN-RL Rew':<12} | {'SNN-RL Succ':<12} | {'New Rew':<12} | {'New Succ':<12}")
print("-" * 75)
for i in range(max(len(c_snnrl), len(c_new))):
    e_range = f"{i*500}-{(i+1)*500}"
    s_rew = c_snnrl[i][2] if i < len(c_snnrl) else 0
    s_suc = c_snnrl[i][3] if i < len(c_snnrl) else 0
    n_rew = c_new[i][2] if i < len(c_new) else 0
    n_suc = c_new[i][3] if i < len(c_new) else 0
    print(f"{e_range:<15} | {s_rew:<12.3f} | {s_suc:<12.3f} | {n_rew:<12.3f} | {n_suc:<12.3f}")

