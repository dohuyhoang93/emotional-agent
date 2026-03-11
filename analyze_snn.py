import json
import statistics

def inspect_checkpoint():
    file_path = 'results/multi_agent_complex_maze/checkpoint_ep_400/agent_0_snn.json'
    print(f"\n--- SNN Checkpoint Analysis ({file_path}) ---")
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        print(f"Metrics (trong SNN): {data.get('metrics', {})}")
        
        neurons = data.get('neurons', [])
        if neurons:
            print(f"Neurons Count: {len(neurons)}")
            thresholds = [n.get('threshold', 0) for n in neurons]
            fire_counts = [n.get('fire_count', 0) for n in neurons]
            print(f"Thresholds -> Avg: {statistics.mean(thresholds):.4f}, Min: {min(thresholds):.4f}, Max: {max(thresholds):.4f}")
            print(f"Fire Counts -> Sum: {sum(fire_counts)}, Avg: {statistics.mean(fire_counts):.2f}, Max: {max(fire_counts)}")
            
        synapses = data.get('synapses', [])
        print(f"Synapses Count: {len(synapses)}")
        if synapses:
            weights = [s.get('weight', 0) for s in synapses]
            if weights:
                print(f"Weights    -> Avg: {statistics.mean(weights):.4e}, Min: {min(weights):.4e}, Max: {max(weights):.4e}")
        
    except Exception as e:
        print(f"Error inspecting checkpoint: {e}")

if __name__ == '__main__':
    inspect_checkpoint()
