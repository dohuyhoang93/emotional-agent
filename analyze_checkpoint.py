"""
Quick analysis script for checkpoint data
"""
import json
import numpy as np
from collections import Counter

import argparse
import os

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument('--path', type=str, help='Path to checkpoint JSON file')
parser.add_argument('--episode', type=int, help='Episode number (auto-constructs path)')
parser.add_argument('--agent', type=int, default=0, help='Agent ID (default 0)')
args = parser.parse_args()

# Construct path if not provided
if args.path:
    file_path = args.path
elif args.episode:
    base_dir = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_Check_checkpoints'
    file_path = os.path.join(base_dir, f'checkpoint_ep_{args.episode}', f'agent_{args.agent}_snn.json')
else:
    # Default fallback
    base_dir = r'C:\Users\dohoang\projects\EmotionAgent\results\Optimization_Sanity_Check_checkpoints'
    file_path = os.path.join(base_dir, 'checkpoint_ep_50', 'agent_0_snn.json')

print(f"Loading checkpoint: {file_path}")

try:
    with open(file_path, 'r') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"❌ Error: File not found: {file_path}")
    exit(1)

synapses = data['synapses']
neurons = data['neurons']

print("=" * 60)
print(f"CHECKPOINT ANALYSIS - {file_path}")
print("=" * 60)

# Synapse Analysis
print(f"\n📊 SYNAPSE STATISTICS (Total: {len(synapses)})")
print("-" * 60)

fitnesses = [s['fitness'] for s in synapses]
weights = [s['weight'] for s in synapses]
consecutive_correct = [s['consecutive_correct'] for s in synapses]
consecutive_wrong = [s['consecutive_wrong'] for s in synapses]
commit_states = [s['commit_state'] for s in synapses]

print("Fitness:")
print(f"  - Unique values: {sorted(set(fitnesses))}")
print(f"  - Mean: {np.mean(fitnesses):.4f}")
print(f"  - Std: {np.std(fitnesses):.4f}")
print(f"  - Min/Max: {min(fitnesses):.4f} / {max(fitnesses):.4f}")

print("\nWeights:")
print(f"  - Mean: {np.mean(weights):.4f}")
print(f"  - Std: {np.std(weights):.4f}")
print(f"  - Min/Max: {min(weights):.4f} / {max(weights):.4f}")

print("\nConsecutive Correct:")
print(f"  - Unique values: {sorted(set(consecutive_correct))[:10]}")  # Top 10
print(f"  - Mean: {np.mean(consecutive_correct):.1f}")
print(f"  - Max: {max(consecutive_correct)}")

print("\nConsecutive Wrong:")
print(f"  - Unique values: {sorted(set(consecutive_wrong))}")
print(f"  - Mean: {np.mean(consecutive_wrong):.1f}")

print("\nCommit States:")
commit_counter = Counter(commit_states)
print(f"  - FLUID (0): {commit_counter[0]}")
print(f"  - SOLID (1): {commit_counter[1]}")
print(f"  - REVOKED (2): {commit_counter.get(2, 0)}")

# Neuron Analysis
print(f"\n\n🧠 NEURON STATISTICS (Total: {len(neurons)})")
print("-" * 60)

fire_counts = [n['fire_count'] for n in neurons]
thresholds = [n['threshold'] for n in neurons]

print("Fire Counts:")
print(f"  - Mean: {np.mean(fire_counts):.1f}")
print(f"  - Std: {np.std(fire_counts):.1f}")
print(f"  - Min/Max: {min(fire_counts)} / {max(fire_counts)}")
print(f"  - Neurons with 0 fires: {sum(1 for fc in fire_counts if fc == 0)}")
print(f"  - Neurons with >15 fires: {sum(1 for fc in fire_counts if fc > 15)}")

print("\nThresholds:")
print(f"  - Mean: {np.mean(thresholds):.4f}")
print(f"  - Std: {np.std(thresholds):.4f}")
print(f"  - Min/Max: {min(thresholds):.4f} / {max(thresholds):.4f}")

# Critical Issues
print("\n\n⚠️  CRITICAL ISSUES DETECTED")
print("=" * 60)

issues = []

if len(set(fitnesses)) == 1:
    issues.append(f"❌ ALL synapses have identical fitness = {fitnesses[0]}")
    issues.append("   → Neural Darwinism selection is INEFFECTIVE")

if max(consecutive_correct) > 10000:
    issues.append(f"❌ Consecutive_correct = {max(consecutive_correct)} is ABNORMALLY HIGH")
    issues.append(f"   → This is ~{max(consecutive_correct)/100:.0f}x the episode count (150)")
    issues.append("   → Commitment mechanism may be counting STEPS instead of EPISODES")

if commit_counter[1] == 0:
    issues.append("❌ NO SOLID synapses found")
    issues.append("   → Commitment mechanism not working")
elif commit_counter[1] == len(synapses):
    issues.append(f"❌ ALL {len(synapses)} synapses are SOLID")
    issues.append("   → Over-commitment, no plasticity left")

if np.std(weights) < 0.05:
    issues.append(f"❌ Weight variance too low (std={np.std(weights):.4f})")
    issues.append("   → Network may have converged to uniform state")

if issues:
    for issue in issues:
        print(issue)
else:
    print("✅ No critical issues detected")

print("\n" + "=" * 60)
