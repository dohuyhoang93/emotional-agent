import json
import os

filepath = r'C:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl'
lines = []
with open(filepath, 'r') as f:
    for line in f:
        if line.strip():
            lines.append(json.loads(line))

print(f'Total episodes: {len(lines)}')

keys = ['avg_reward', 'success_rate', 'epsilon', 'maturity', 'avg_firing_rate', 'debug_total_synapses', 'neural_loss_avg', 'avg_q_predicted', 'debug_process_memory_mb']
results = {}
for k in keys:
    vals = [x['metrics'].get(k) for x in lines if k in x['metrics'] and x['metrics'][k] is not None]
    if vals:
        results[k] = {
            'min': min(vals), 
            'max': max(vals), 
            'avg': sum(vals)/len(vals), 
            'first': vals[0], 
            'last': vals[-1]
        }
        print(f'{k}: {results[k]}')
