import json
import os
import sys

def inspect_memory():
    # Find latest checkpoint
    res_dir = "results/memory_dump_test_checkpoints"
    if not os.path.exists(res_dir):
        print(f"Directory not found: {res_dir}")
        return

    filepath = os.path.join(res_dir, "agent_0_snn.json")
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return

    with open(filepath, 'r') as f:
        data = json.load(f)

    print("\n=== BRAIN DUMP: AGENT 0 ===")
    
    print(f"\n[1] METADATA")
    print(json.dumps(data['metadata'], indent=2))
    
    print(f"\n[2] PROCEDURAL MEMORY (SNN Synapses)")
    synapses = data['synapses']
    print(f"Total Synapses: {len(synapses)}")
    if synapses:
        print("Sample Synapse [0]:")
        print(json.dumps(synapses[0], indent=2))
    
    print(f"\n[3] PROCEDURAL MEMORY (Q-Table)")
    q_table = data.get('memory', {}).get('q_table', {})
    print(f"Known States: {len(q_table)}")
    # Print first few entries
    for k, v in list(q_table.items())[:3]:
        print(f"  State {k}: {v}")

    print(f"\n[4] SEMANTIC MEMORY (Beliefs)")
    beliefs = data.get('memory', {}).get('beliefs', {})
    print(json.dumps(beliefs, indent=2))
    
    print(f"\n[5] EPISODIC/SHORT-TERM (Recent Buffer)")
    stm = data.get('memory', {}).get('short_term', [])
    for event in stm:
        print(f"  {event}")
        
    print("\n===========================")

if __name__ == "__main__":
    inspect_memory()
