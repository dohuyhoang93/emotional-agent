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

def summarize(metrics):
    if not metrics:
        return {}
    
    # Lấy 500 tập cuối để đánh giá hiệu suất hội tụ
    recent = metrics[-500:]
    
    avg_reward_recent = np.mean([m['metrics'].get('avg_reward', 0) for m in recent])
    success_rate_recent = np.mean([m['metrics'].get('success_rate', 0) for m in recent])
    
    avg_firing = np.mean([m['metrics'].get('avg_firing_rate', 0) for m in recent])
    synapses = np.mean([m['metrics'].get('debug_total_synapses', 0) for m in recent])
    loss = np.mean([m['metrics'].get('neural_loss_avg', 0) for m in recent])
    q_pred = np.mean([m['metrics'].get('avg_q_predicted', 0) for m in recent])
    
    # Tính thời gian (nếu có datetime)
    try:
        from datetime import datetime
        start = datetime.fromisoformat(metrics[0]['timestamp'])
        end = datetime.fromisoformat(metrics[-1]['timestamp'])
        duration = (end - start).total_seconds()
    except:
        duration = 0
        
    return {
        'total_episodes': len(metrics),
        'duration_sec': duration,
        'avg_reward_last500': avg_reward_recent,
        'success_rate_last500': success_rate_recent,
        'avg_firing_rate': avg_firing,
        'synapses_avg': synapses,
        'neural_loss': loss,
        'q_predicted_avg': q_pred
    }

old_path = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_DeepRL\metrics.jsonl'
new_path = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_DeepRL_Path_Darwinism\metrics.jsonl'

old_m = load_metrics(old_path)
new_m = load_metrics(new_path)

res_old = summarize(old_m)
res_new = summarize(new_m)

print('--- OLD (Blind Darwinism) ---')
for k, v in res_old.items():
    print(f'{k}: {v}')
    
print('\n--- NEW (Reward-based Darwinism) ---')
for k, v in res_new.items():
    print(f'{k}: {v}')
