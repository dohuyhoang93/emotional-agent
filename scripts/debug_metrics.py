import json

# Load metrics
with open('logs/snn_baseline_run_1_metrics.json', 'r') as f:
    data = json.load(f)

metrics = data.get('metrics', [])
summary = data.get('summary', {})

print("=" * 60)
print("AUDIT TRAIL ANALYSIS")
print("=" * 60)

# Overall summary
print("\n1. EXPERIMENT SUMMARY:")
print(f"   Total Episodes: {len(metrics)}")
print(f"   Avg Reward: {summary.get('avg_reward', 0):.4f}")
print(f"   Best Reward: {summary.get('best_reward', 0):.4f}")
print(f"   Duration: {summary.get('duration', 0):.2f}s")
print(f"   Avg Episode Time: {summary.get('avg_episode_time', 0):.2f}s")

# Check first and last episodes
if metrics:
    print("\n2. FIRST EPISODE (Episode 0):")
    first = metrics[0]
    print(f"   Avg Reward: {first.get('avg_reward', 0):.4f}")
    print(f"   Best Reward: {first.get('best_reward', 0):.4f}")
    print(f"   Agents: {first.get('num_agents', 0)}")
    
    print("\n3. LAST EPISODE (Episode 99):")
    last = metrics[-1]
    print(f"   Avg Reward: {last.get('avg_reward', 0):.4f}")
    print(f"   Best Reward: {last.get('best_reward', 0):.4f}")
    print(f"   Agents: {last.get('num_agents', 0)}")

# Check for any non-zero rewards
print("\n4. REWARD ANALYSIS:")
non_zero_rewards = [m for m in metrics if m.get('avg_reward', 0) != 0.0 or m.get('best_reward', 0) != 0.0]
print(f"   Episodes with non-zero reward: {len(non_zero_rewards)}")

if non_zero_rewards:
    print("   First non-zero reward episode:")
    print(f"      Episode: {non_zero_rewards[0].get('episode', 0)}")
    print(f"      Avg Reward: {non_zero_rewards[0].get('avg_reward', 0):.4f}")
else:
    print("   ❌ NO AGENTS REACHED GOAL IN 100 EPISODES!")

# Social learning check
print("\n5. SOCIAL LEARNING:")
total_transfers = sum(m.get('social_learning_transfers', 0) for m in metrics)
total_synapses = sum(m.get('social_learning_synapses', 0) for m in metrics)
print(f"   Total Transfers: {total_transfers}")
print(f"   Total Synapses: {total_synapses}")
print(f"   Status: {'✅ Active' if total_transfers > 0 else '❌ Disabled (expected for baseline)'}")

# Revolution check
print("\n6. REVOLUTION PROTOCOL:")
total_revolutions = sum(m.get('revolutions', 0) for m in metrics)
print(f"   Total Revolutions: {total_revolutions}")
print(f"   Status: {'✅ Active' if total_revolutions > 0 else '❌ Disabled (expected for baseline)'}")

print("\n" + "=" * 60)
print("ROOT CAUSE ANALYSIS")
print("=" * 60)

print("\n🔍 DIAGNOSIS:")
print("   1. 0% success rate = Agents không tìm thấy goal")
print("   2. Maze: 25×25, Start: [0,0], Goal: [24,24]")
print("   3. Max steps: 500 (Manhattan distance = 48)")
print("   4. 100 episodes không đủ để học maze phức tạp")
print("\n💡 RECOMMENDATIONS:")
print("   A) Tăng episodes: 100 → 500 hoặc 5000")
print("   B) Simplify maze: 25×25 → 15×15 (test)")
print("   C) Add intermediate rewards (distance-based)")
print("   D) Increase exploration time (slower decay)")

print("\n" + "=" * 60)
