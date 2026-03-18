import json
import statistics
import os

def analyze():
    episodes = []
    firing_rates = []
    rewards = []
    success_rates = []
    synapses = []
    memory = []
    
    file_path = r'C:\Users\dohoang\projects\EmotionAgent\results\multi_agent_complex_maze\metrics.jsonl'
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                data = json.loads(line)
                # Filter out restarts if necessary, but here we just take all to see the whole history
                ep = data.get('episode', -1)
                metrics = data.get('metrics', {})
                
                episodes.append(ep)
                firing_rates.append(metrics.get('avg_firing_rate', 0.0))
                rewards.append(metrics.get('avg_reward', 0.0))
                success_rates.append(metrics.get('success_rate', 0.0))
                synapses.append(metrics.get('debug_total_synapses', 0))
                memory.append(metrics.get('debug_process_memory_mb', 0))
            except json.JSONDecodeError:
                pass
                
    if not episodes:
        print("No valid metrics found.")
        return
        
    print(f"Tổng số bản ghi (Log entries): {len(episodes)}")
    print(f"Episode cuối cùng: {episodes[-1]}")
    
    print(f"\n--- Tỉ lệ thành công (Success Rate) ---")
    print(f"  Trung bình 20 ep đầu: {statistics.mean(success_rates[:20]):.2%}")
    print(f"  Trung bình 20 ep cuối: {statistics.mean(success_rates[-20:]):.2%}")
    print(f"  Max: {max(success_rates):.2%} (Ep {episodes[success_rates.index(max(success_rates))]})")
    
    print(f"\n--- Firing Rate (SNN) ---")
    print(f"  Trung bình 20 ep đầu: {statistics.mean(firing_rates[:20]):.4f}")
    print(f"  Trung bình 20 ep cuối: {statistics.mean(firing_rates[-20:]):.4f}")
    print(f"  Biến thiên (Max/Min): {max(firing_rates):.4f} / {min(firing_rates):.4f}")
    
    print(f"\n--- Rewards (Phần thưởng) ---")
    print(f"  Trung bình 20 ep đầu: {statistics.mean(rewards[:20]):.2f}")
    print(f"  Trung bình 20 ep cuối: {statistics.mean(rewards[-20:]):.2f}")
    print(f"  Max Reward: {max(rewards):.2f} (Ep {episodes[rewards.index(max(rewards))]})")
    
    print(f"\n--- Synapses (Kết nối thần kinh) ---")
    print(f"  Ban đầu: {synapses[0]}")
    print(f"  Cuối cùng: {synapses[-1]}")
    print(f"  Max: {max(synapses)} (Ep {episodes[synapses.index(max(synapses))]})")

    print(f"\n--- Memory Usage (Bộ nhớ hệ thống) ---")
    print(f"  Max: {max(memory):.2f} MB")
    print(f"  Cuối cùng: {memory[-1]:.2f} MB")

    print("\n--- Diễn biến qua thời gian (Lấy mẫu mỗi ~20 bản ghi) ---")
    step = max(1, len(episodes) // 15)
    print(f"{'Ep':>5} | {'Reward':>8} | {'Success':>8} | {'Firing':>8} | {'Synapses':>8}")
    print("-" * 50)
    for i in range(0, len(episodes), step):
        print(f"{episodes[i]:5d} | {rewards[i]:8.2f} | {success_rates[i]:8.2%} | {firing_rates[i]:8.4f} | {synapses[i]:8d}")
        
if __name__ == '__main__':
    analyze()
