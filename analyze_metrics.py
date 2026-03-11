import json
import statistics

def analyze():
    episodes = []
    firing_rates = []
    rewards = []
    synapses = []
    
    with open('results/multi_agent_complex_maze/metrics.jsonl', 'r') as f:
        for line in f:
            if not line.strip(): continue
            try:
                data = json.loads(line.strip())
                ep = data.get('episode', -1)
                metrics = data.get('metrics', {})
                
                episodes.append(ep)
                firing_rates.append(metrics.get('avg_firing_rate', 0.0))
                rewards.append(metrics.get('avg_reward', 0.0))
                synapses.append(metrics.get('debug_total_synapses', 0))
            except json.JSONDecodeError:
                pass
                
    if not episodes:
        print("No valid metrics found.")
        return
        
    print(f"Total Episodes Analyzed: {len(episodes)}")
    print(f"--- Firing Rate ---")
    print(f"  First 10 Avg: {statistics.mean(firing_rates[:10]):.2e}")
    print(f"  Last 10 Avg:  {statistics.mean(firing_rates[-10:]):.2e}")
    print(f"  Max: {max(firing_rates):.2e} (Ep {episodes[firing_rates.index(max(firing_rates))]})")
    
    print(f"\n--- Rewards ---")
    print(f"  First 10 Avg: {statistics.mean(rewards[:10]):.2f}")
    print(f"  Last 10 Avg:  {statistics.mean(rewards[-10:]):.2f}")
    print(f"  Max: {max(rewards):.2f} (Ep {episodes[rewards.index(max(rewards))]})")
    
    print(f"\n--- Synapses ---")
    print(f"  First 10 Avg: {statistics.mean(synapses[:10]):.0f}")
    print(f"  Last 10 Avg:  {statistics.mean(synapses[-10:]):.0f}")
    print(f"  Max: {max(synapses)} (Ep {episodes[synapses.index(max(synapses))]})")

    print("\n--- Trend over time (Sampling every ~40 episodes) ---")
    step = max(1, len(episodes) // 10)
    for i in range(0, len(episodes), step):
        print(f"Ep {episodes[i]:4d}: Reward={rewards[i]:7.2f} | Firing Rate={firing_rates[i]:.2e} | Synapses={synapses[i]}")
        
if __name__ == '__main__':
    analyze()
