"""
Debug Script - Why Neurons Not Firing?
=======================================
Investigate tại sao SNN neurons không bắn.

Author: Do Huy Hoang  
Date: 2025-12-25
"""
import json
import numpy as np
from environment import GridWorld
from src.adapters.environment_adapter import EnvironmentAdapter
from src.core.context import SystemContext, DomainContext, GlobalContext
from src.core.snn_context_theus import SNNSystemContext, SNNGlobalContext, SNNDomainContext, NeuronState, SynapseState
from src.processes.p1_perception import perception
from src.processes.snn_rl_bridge import encode_state_to_spikes

def create_simple_snn():
    """Tạo SNN đơn giản để debug."""
    global_ctx = SNNGlobalContext(num_neurons=10, vector_dim=16, connectivity=0.3, seed=42)
    domain_ctx = SNNDomainContext(global_ctx)
    
    # Create 10 neurons
    for i in range(10):
        neuron = NeuronState(
            neuron_id=i,
            prototype_vector=np.random.randn(16).astype(np.float32),
            threshold=1.0  # Default threshold
        )
        domain_ctx.neurons.append(neuron)
    
    return SNNSystemContext(global_ctx, domain_ctx)

def debug_firing():
    """Debug firing mechanism."""
    print("=" * 70)
    print("DEBUG: WHY NEURONS NOT FIRING?")
    print("=" * 70)
    
    # Setup
    with open('multi_agent_complex_maze.json', 'r') as f:
        config = json.load(f)
    
    env_config = config['experiments'][0]['parameters']['environment_config']
    env = GridWorld(env_config)
    env.reset()
    adapter = EnvironmentAdapter(env)
    
    rl_ctx = SystemContext(GlobalContext(), DomainContext())
    snn_ctx = create_simple_snn()
    
    print("\n1. INITIAL STATE:")
    print(f"   Neurons: {len(snn_ctx.domain_ctx.neurons)}")
    for i, n in enumerate(snn_ctx.domain_ctx.neurons[:3]):
        print(f"   Neuron {i}: threshold={n.threshold:.2f}, potential={n.potential:.2f}")
    
    # Get sensor vector
    print("\n2. SENSOR VECTOR:")
    perception(rl_ctx, adapter, agent_id=0)
    obs = rl_ctx.domain_ctx.current_observation
    print(f"   Type: {type(obs)}")
    print(f"   Shape: {obs.shape if isinstance(obs, np.ndarray) else 'N/A'}")
    print(f"   Values: {obs[:5] if isinstance(obs, np.ndarray) else obs}")
    
    # Encode to SNN
    print("\n3. ENCODE TO SNN:")
    print("   Before encoding:")
    for i, n in enumerate(snn_ctx.domain_ctx.neurons[:3]):
        print(f"   Neuron {i}: potential={n.potential:.2f}")
    
    encode_state_to_spikes(rl_ctx, snn_ctx)
    
    print("\n   After encoding:")
    for i, n in enumerate(snn_ctx.domain_ctx.neurons[:3]):
        print(f"   Neuron {i}: potential={n.potential:.2f}, potential_vector={n.potential_vector[:3]}")
    
    # Check firing
    print("\n4. CHECK FIRING:")
    fired_count = 0
    for i, n in enumerate(snn_ctx.domain_ctx.neurons):
        if n.potential >= n.threshold:
            print(f"   ✅ Neuron {i} FIRED! (potential={n.potential:.2f} >= threshold={n.threshold:.2f})")
            fired_count += 1
        elif i < 3:
            print(f"   ❌ Neuron {i} NOT FIRED (potential={n.potential:.2f} < threshold={n.threshold:.2f})")
    
    print(f"\n   Total fired: {fired_count}/{len(snn_ctx.domain_ctx.neurons)}")
    
    # Diagnosis
    print("\n5. DIAGNOSIS:")
    if fired_count == 0:
        print("   ⚠️ NO NEURONS FIRED!")
        print("\n   Possible causes:")
        print("   1. Input potential too weak")
        print("   2. Threshold too high")
        print("   3. Encoding not working")
        
        # Check encoding
        print("\n   Checking encoding in snn_rl_bridge.py...")
        print("   Current code:")
        print("   ```")
        print("   neuron.potential = sensor_vector[i] * 2.0")
        print("   ```")
        
        max_potential = max(n.potential for n in snn_ctx.domain_ctx.neurons)
        min_threshold = min(n.threshold for n in snn_ctx.domain_ctx.neurons)
        
        print(f"\n   Max potential: {max_potential:.2f}")
        print(f"   Min threshold: {min_threshold:.2f}")
        
        if max_potential < min_threshold:
            print(f"\n   🔍 FOUND ISSUE: Max potential ({max_potential:.2f}) < Min threshold ({min_threshold:.2f})")
            print("   SOLUTION: Increase amplification factor!")
            print("   Suggest: neuron.potential = sensor_vector[i] * 5.0")
    else:
        print(f"   ✅ {fired_count} neurons fired successfully!")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    try:
        debug_firing()
    except Exception as e:
        print(f"\n❌ DEBUG FAILED: {e}")
        import traceback
        traceback.print_exc()
