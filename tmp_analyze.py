import json
import statistics

filepath = r"c:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl"

try:
    with open(filepath, "r") as f:
        lines = f.readlines()
        
    last_19 = lines[-19:]
    
    episodes = []
    rewards = []
    successes = []
    firing_rates = []
    q_table_sizes = []
    
    for line in last_19:
        data = json.loads(line)
        metrics = data.get("metrics", {})
        episodes.append(data.get("episode"))
        rewards.append(metrics.get("avg_reward", 0))
        successes.append(metrics.get("success_rate", 0))
        firing_rates.append(metrics.get("avg_firing_rate", 0))
        q_table_sizes.append(metrics.get("debug_q_table_size", 0))
        
    print(f"--- THỐNG KÊ 19 PHIÊN CUỐI CÙNG ---")
    print(f"Các tập (episodes): {episodes[0]} đến {episodes[-1]}")
    print(f"Average Reward: {statistics.mean(rewards):.2f} (Min: {min(rewards):.2f}, Max: {max(rewards):.2f})")
    print(f"Success Rate: {statistics.mean(successes)*100:.2f}% (Min: {min(successes)*100:.2f}%, Max: {max(successes)*100:.2f}%)")
    print(f"Avg Firing Rate: {statistics.mean(firing_rates):.6f} (Min: {min(firing_rates):.6f}, Max: {max(firing_rates):.6f})")
    print(f"Q-Table Size (cuối cùng): {q_table_sizes[-1]}")
    
except Exception as e:
    print(f"Lỗi: {e}")
