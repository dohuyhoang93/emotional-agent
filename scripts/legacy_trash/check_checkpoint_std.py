import json
import numpy as np

try:
    with open('results/Optimization_Sanity_Check_checkpoints/checkpoint_ep_50/agent_0_snn.json', 'r') as f:
        data = json.load(f)
        
    neurons = data.get('neurons', [])
    thresholds = [n.get('threshold', 0.0) for n in neurons]
    
    if not thresholds:
        print("No neurons found")
    else:
        mean_thresh = np.mean(thresholds)
        std_thresh = np.std(thresholds)
        print(f"Neurons count: {len(neurons)}")
        print(f"Threshold stats: Mean={mean_thresh:.6f}, Std={std_thresh:.6f}")
        print(f"Sample thresholds: {thresholds[:5]}")
        
except Exception as e:
    print(f"Error: {e}")
