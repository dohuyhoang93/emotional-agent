import json
import os
import sys

def main():
    path = r'results/Optimization_Sanity_Check_checkpoints/metrics.jsonl'
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    print("Reading metrics...")
    rewards = []
    steps = []
    
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    m = data.get('metrics', {})
                    rewards.append(m.get('avg_reward', 0))
                    steps.append(m.get('episode_length', 100)) # Default 100 if missing
                except:
                    continue
    
    total = len(rewards)
    if total == 0:
        print("No data found.")
        return

    avg_first = sum(rewards[:100]) / min(100, total)
    avg_last = sum(rewards[-100:]) / min(100, total)
    max_r = max(rewards)
    
    # Calculate simple moving average trend
    window = 100
    if total > window:
        trend = "Improving" if avg_last > avg_first else "Degrading"
    else:
        trend = "Insufficient Data"

    print("-" * 30)
    print(f"Total Episodes: {total}")
    print(f"First 100 Avg Reward: {avg_first:.2f}")
    print(f"Last 100 Avg Reward:  {avg_last:.2f}")
    print(f"Max Reward:           {max_r:.2f}")
    print(f"Trend:                {trend}")
    print("-" * 30)

if __name__ == "__main__":
    main()
