import json
import numpy as np
import os

checkpoint_path = "results/Optimization_Sanity_Check_checkpoints/checkpoint_ep_50/agent_0_snn.json"

try:
    if not os.path.exists(checkpoint_path):
        print(f"File not found: {checkpoint_path}")
        exit(1)
        
    with open(checkpoint_path, 'r') as f:
        data = json.load(f)
        
    # Check structure: Theus context usually has 'domain_ctx' -> 'neurons'
    # or it might be serialized differently. Let's inspect keys if fails.
    
    # Direct access for checkpoint format
    if 'neurons' in data:
        neurons = data['neurons']
        thresholds = [n.get('threshold', 0.0) for n in neurons]
        
        thresholds = np.array(thresholds)
        
        print(f"Count: {len(thresholds)}")
        print(f"Min: {np.min(thresholds)}")
        print(f"Max: {np.max(thresholds)}")
        print(f"Mean: {np.mean(thresholds)}")
        print(f"StdDev: {np.std(thresholds)}")
        
        if np.std(thresholds) > 1e-4:
            print("SUCCESS: Significant threshold diversity detected.")
        else:
            print("FAILURE: Thresholds are effectively uniform.")
            
    elif 'domain_ctx' in data and 'neurons' in data['domain_ctx']:
        print("Structure mismatch. Keys found:", data.keys())

except Exception as e:
    print(f"Error processing checkpoint: {e}")
