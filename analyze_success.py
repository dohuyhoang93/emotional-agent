import json
import os

def main():
    path = r'results/Optimization_Sanity_Check_checkpoints/metrics.jsonl'
    if not os.path.exists(path):
        print("File not found")
        return

    print("Analyzing Success Rate...")
    success_count = 0
    last_100_success = 0
    total = 0
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        total = len(lines)
        for i, line in enumerate(lines):
            if not line.strip(): continue
            try:
                data = json.loads(line)
                metrics = data.get('metrics', {})
                # 'agent_success' is list of bools [False, False...]
                # If ANY agent succeeded, count as episode success? Or require ALL?
                # Usually in single-goal maze, 1 agent success = success
                ag_success = metrics.get('agent_success', [])
                is_success = any(ag_success)
                
                if is_success:
                    success_count += 1
                    if i >= total - 100:
                        last_100_success += 1
            except:
                continue

    last_100_count = min(100, total)
    
    print("-" * 30)
    print(f"Total Episodes: {total}")
    print(f"Global Success Rate:       {success_count/total*100:.2f}%")
    if last_100_count > 0:
        print(f"Last 100 Ep Success Rate:  {last_100_success/last_100_count*100:.2f}%")
    else:
        print("Insufficient data for last 100")
    print("-" * 30)

if __name__ == "__main__":
    main()
