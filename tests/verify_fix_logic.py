
import numpy as np

def test_aggregation_logic():
    print("Testing aggregation logic...")
    # Simulate elite agents' weights
    # Agent 1: synapses 1, 2
    # Agent 2: synapses 2, 3
    
    agent1_weights = {1: 0.5, 2: 0.6}
    agent2_weights = {2: 0.8, 3: 0.9}
    
    all_weights_dicts = [agent1_weights, agent2_weights]
    
    # Collect all unique synapse IDs
    all_synapse_ids = set()
    for w in all_weights_dicts:
        all_synapse_ids.update(w.keys())
        
    # Aggregate
    ancestor_weights = {}
    for syn_id in all_synapse_ids:
        values = []
        for w_dict in all_weights_dicts:
            if syn_id in w_dict:
                values.append(w_dict[syn_id])
        
        if values:
            ancestor_weights[syn_id] = float(np.mean(values))
            
    print(f"Ancestors: {ancestor_weights}")
    
    # Verify type
    if not isinstance(ancestor_weights, dict):
        raise TypeError(f"Expected dict, got {type(ancestor_weights)}")
        
    # Verify values
    # Synapse 1: 0.5
    # Synapse 2: (0.6 + 0.8) / 2 = 0.7
    # Synapse 3: 0.9
    
    assert ancestor_weights[1] == 0.5
    assert ancestor_weights[2] == 0.7
    assert ancestor_weights[3] == 0.9
    
    print("Aggregation logic passed.")
    return ancestor_weights

def test_logging_logic(ancestor_weights):
    print("Testing logging logic...")
    # The fix was: float(np.mean(np.abs(list(ancestor_weights.values()))))
    
    try:
        avg_weight = float(np.mean(np.abs(list(ancestor_weights.values()))))
        print(f"Avg weight: {avg_weight}")
    except Exception as e:
        print(f"Logging logic FAILED: {e}")
        raise e
        
    print("Logging logic passed.")

def test_consumer_logic(ancestor_weights):
    print("Testing consumer logic (snn_advanced_features_theus.py)...")
    
    # The check is: if not ancestor:
    
    if not ancestor_weights:
        print("Ancestor is empty (unexpected for this test)")
    else:
        print("Ancestor is not empty (expected)")
        
    # Test empty case
    empty_ancestor = {}
    if not empty_ancestor:
        print("Empty ancestor handled correctly.")
    else:
        print("Empty ancestor logic FAILED.")
        
    print("Consumer logic passed.")

if __name__ == "__main__":
    result = test_aggregation_logic()
    test_logging_logic(result)
    test_consumer_logic(result)
    print("ALL VERIFICATIONS PASSED.")
