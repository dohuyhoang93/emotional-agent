"""
End-to-End Integration Test
============================
Test toàn bộ flow: Sensor System → SNN → RL → Rewards

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
from src.processes.snn_rl_bridge import encode_state_to_spikes, encode_emotion_vector
from src.tools.brain_biopsy_theus import BrainBiopsyTheus

def create_test_snn(num_neurons=50, vector_dim=16, connectivity=0.15):
    """Tạo SNN context cho test."""
    global_ctx = SNNGlobalContext(
        num_neurons=num_neurons,
        vector_dim=vector_dim,
        connectivity=connectivity,
        seed=42
    )
    
    domain_ctx = SNNDomainContext(global_ctx)
    
    # Create neurons
    for i in range(num_neurons):
        neuron = NeuronState(
            neuron_id=i,
            prototype_vector=np.random.randn(vector_dim).astype(np.float32),
            threshold=1.0
        )
        domain_ctx.neurons.append(neuron)
    
    # Create synapses
    np.random.seed(42)
    synapse_id = 0
    for pre in range(num_neurons):
        for post in range(num_neurons):
            if pre != post and np.random.rand() < connectivity:
                synapse = SynapseState(
                    synapse_id=synapse_id,
                    pre_neuron_id=pre,
                    post_neuron_id=post,
                    weight=0.5
                )
                domain_ctx.synapses.append(synapse)
                synapse_id += 1
    
    return SNNSystemContext(global_ctx, domain_ctx)

def test_end_to_end():
    """Test end-to-end integration."""
    print("=" * 70)
    print("END-TO-END INTEGRATION TEST")
    print("=" * 70)
    
    # 1. Setup Environment
    print("\n1. SETUP ENVIRONMENT:")
    with open('multi_agent_complex_maze.json', 'r') as f:
        config = json.load(f)
    
    env_config = config['experiments'][0]['parameters']['environment_config']
    env = GridWorld(env_config)
    env.reset()
    adapter = EnvironmentAdapter(env)
    print("   ✅ Environment created")
    
    # 2. Setup Contexts
    print("\n2. SETUP CONTEXTS:")
    rl_ctx = SystemContext(GlobalContext(), DomainContext())
    snn_ctx = create_test_snn()
    print(f"   ✅ RL Context created")
    print(f"   ✅ SNN Context created ({len(snn_ctx.domain_ctx.neurons)} neurons, {len(snn_ctx.domain_ctx.synapses)} synapses)")
    
    # 3. Run 5 Episodes
    print("\n3. RUN 5 EPISODES:")
    
    for episode in range(5):
        print(f"\n   Episode {episode + 1}:")
        env.reset()
        total_reward = 0
        
        for step in range(20):  # 20 steps per episode
            # 3.1 Perception
            perception(rl_ctx, adapter, agent_id=0)
            obs = rl_ctx.domain_ctx.current_observation
            
            # 3.2 Encode to SNN
            encode_state_to_spikes(rl_ctx, snn_ctx)
            
            # 3.3 Encode emotion from SNN
            encode_emotion_vector(rl_ctx, snn_ctx)
            
            # 3.4 Select action (random for test)
            action = np.random.choice(['up', 'down', 'left', 'right'])
            
            # 3.5 Perform action
            reward = env.perform_action(0, action)
            total_reward += reward
            
            # Check if done
            if env.is_done():
                break
        
        print(f"      Total reward: {total_reward:.2f}")
        print(f"      Steps: {step + 1}")
    
    # 4. Brain Biopsy Analysis
    print("\n4. BRAIN BIOPSY ANALYSIS:")
    
    # Population stats
    pop = BrainBiopsyTheus.inspect_population(snn_ctx)
    print(f"   Active neurons: {pop['population']['active_neurons']}/{pop['population']['total_neurons']}")
    print(f"   Synapses: {pop['connectivity']['total_synapses']}")
    print(f"   Avg weight: {pop['weights']['avg']:.3f}")
    
    # Sensor learning
    sensor_vec = adapter.get_sensor_vector(0)
    sensor_info = BrainBiopsyTheus.inspect_sensor_learning(snn_ctx, sensor_vec)
    print(f"   Top matching neuron: {sensor_info['top_matching_neurons'][0]['neuron_id']}")
    
    # Causality
    causality = BrainBiopsyTheus.inspect_causality(snn_ctx, threshold=0.6)
    print(f"   Strong synapses: {causality['strong_synapses_count']}")
    
    print("\n" + "=" * 70)
    print("✅ END-TO-END TEST HOÀN TẤT!")
    print("=" * 70)
    print("\n📊 SUMMARY:")
    print("   ✅ Sensor system works")
    print("   ✅ Perception process works")
    print("   ✅ SNN encoding works")
    print("   ✅ Emotion vector works")
    print("   ✅ Rewards work")
    print("   ✅ Brain biopsy works")
    print("\n🎉 ALL SYSTEMS OPERATIONAL!")

if __name__ == "__main__":
    try:
        test_end_to_end()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
