import json
import os

metrics_file = "results/Optimization_Sanity_Check_checkpoints/metrics.jsonl"

try:
    with open(metrics_file, 'r') as f:
        lines = f.readlines()
        if not lines:
            print("File is empty")
            exit(1)
            
        last_line = lines[-1]
        data = json.loads(last_line)
        metrics = data.get("metrics", {})
        
        std_th = metrics.get("std_threshold", 0.0)
        avg_th = metrics.get("avg_threshold", 0.0)
        
        print(f"std_threshold: {std_th}")
        print(f"avg_threshold: {avg_th}")
        
        if std_th > 0:
            print("SUCCESS: Threshold diversity detected.")
        else:
            print("FAILURE: Thresholds are uniform.")
            
except Exception as e:
    print(f"Error reading metrics: {e}")
