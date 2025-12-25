"""
Production Experiment Runner - 100 Episodes
============================================
Chạy 100 episodes với brain biopsy analysis.
Thu thập data để verify causality learning.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import json
import numpy as np
import os
from datetime import datetime
from environment import GridWorld
from src.adapters.environment_adapter import EnvironmentAdapter
from src.core.context import SystemContext, DomainContext, GlobalContext
from src.core.snn_context_theus import SNNSystemContext, SNNGlobalContext, SNNDomainContext, NeuronState, SynapseState
from src.processes.p1_perception import perception
from src.processes.snn_rl_bridge import encode_state_to_spikes, encode_emotion_vector
from src.tools.brain_biopsy_theus import BrainBiopsyTheus
from src.utils.snn_persistence import save_snn_agent

def create_snn(num_neurons=50, vector_dim=16, connectivity=0.15, seed=42):
    """Tạo SNN context."""
    global_ctx = SNNGlobalContext(
        num_neurons=num_neurons,
        vector_dim=vector_dim,
        connectivity=connectivity,
        seed=seed
    )
    
    domain_ctx = SNNDomainContext(global_ctx)
    
    # Create neurons
    np.random.seed(seed)
    for i in range(num_neurons):
        neuron = NeuronState(
            neuron_id=i,
            prototype_vector=np.random.randn(vector_dim).astype(np.float32),
            threshold=1.0
        )
        domain_ctx.neurons.append(neuron)
    
    # Create synapses
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

def run_experiment():
    """Run 100 episodes experiment."""
    print("=" * 70)
    print("PRODUCTION EXPERIMENT - 100 EPISODES")
    print("=" * 70)
    
    # Setup
    print("\n📋 SETUP:")
    with open('multi_agent_complex_maze.json', 'r') as f:
        config = json.load(f)
    
    env_config = config['experiments'][0]['parameters']['environment_config']
    env = GridWorld(env_config)
    adapter = EnvironmentAdapter(env)
    
    rl_ctx = SystemContext(GlobalContext(), DomainContext())
    snn_ctx = create_snn()
    
    print(f"   Environment: {env.size}x{env.size} maze")
    print(f"   SNN: {len(snn_ctx.domain_ctx.neurons)} neurons, {len(snn_ctx.domain_ctx.synapses)} synapses")
    print(f"   Episodes: 100")
    
    # Metrics
    episode_rewards = []
    episode_steps = []
    success_count = 0
    
    # Output dir
    output_dir = f"experiment_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    
    # Run episodes
    print("\n🚀 RUNNING EPISODES:")
    for episode in range(100):
        env.reset()
        total_reward = 0
        steps = 0
        
        for step in range(500):  # Max 500 steps
            # Perception
            perception(rl_ctx, adapter, agent_id=0)
            
            # Encode to SNN
            encode_state_to_spikes(rl_ctx, snn_ctx)
            
            # Get emotion
            encode_emotion_vector(rl_ctx, snn_ctx)
            
            # Simple epsilon-greedy action selection
            epsilon = 0.3 * (0.995 ** episode)  # Decay
            if np.random.rand() < epsilon:
                action = np.random.choice(['up', 'down', 'left', 'right'])
            else:
                # Greedy (random for now, would use Q-values in full implementation)
                action = np.random.choice(['up', 'down', 'left', 'right'])
            
            # Perform action
            reward = env.perform_action(0, action)
            total_reward += reward
            steps += 1
            
            # Check done
            if env.is_done():
                if tuple(env.agent_positions[0]) == env.goal_pos:
                    success_count += 1
                break
        
        episode_rewards.append(total_reward)
        episode_steps.append(steps)
        
        # Progress
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            print(f"   Episode {episode + 1}/100: avg_reward={avg_reward:.2f}, success_rate={success_count/(episode+1)*100:.1f}%")
        
        # Brain biopsy analysis every 25 episodes
        if (episode + 1) % 25 == 0:
            print(f"\n   🔬 BRAIN BIOPSY (Episode {episode + 1}):")
            
            pop = BrainBiopsyTheus.inspect_population(snn_ctx)
            print(f"      Active neurons: {pop['population']['active_neurons']}/{pop['population']['total_neurons']}")
            print(f"      Solid synapses: {pop['connectivity']['solid_synapses']}")
            print(f"      Avg weight: {pop['weights']['avg']:.3f}")
            
            # Save analysis
            analysis_file = os.path.join(output_dir, f'biopsy_ep{episode+1}.json')
            BrainBiopsyTheus.export_to_json(pop, analysis_file)
            print(f"      Saved to: {analysis_file}")
    
    # Final analysis
    print("\n" + "=" * 70)
    print("📊 FINAL RESULTS:")
    print("=" * 70)
    
    print(f"\nPerformance:")
    print(f"   Success rate: {success_count/100*100:.1f}%")
    print(f"   Avg reward: {np.mean(episode_rewards):.2f}")
    print(f"   Avg steps: {np.mean(episode_steps):.1f}")
    
    print(f"\nBrain Biopsy:")
    pop = BrainBiopsyTheus.inspect_population(snn_ctx)
    print(f"   Active neurons: {pop['population']['active_neurons']}/{pop['population']['total_neurons']}")
    print(f"   Solid synapses: {pop['connectivity']['solid_synapses']}")
    print(f"   Avg weight: {pop['weights']['avg']:.3f}")
    
    # Causality analysis
    sensor_vec = adapter.get_sensor_vector(0)
    causality = BrainBiopsyTheus.inspect_causality(snn_ctx, threshold=0.6)
    print(f"\nCausality:")
    print(f"   Strong synapses: {causality['strong_synapses_count']}")
    print(f"   Sensor→Hidden: {causality['patterns']['sensor_to_hidden']}")
    
    # Save trained agent
    agent_file = save_snn_agent(snn_ctx, 0, output_dir)
    print(f"\n💾 Saved trained agent: {agent_file}")
    
    # Save metrics
    metrics = {
        'episode_rewards': episode_rewards,
        'episode_steps': episode_steps,
        'success_count': success_count,
        'success_rate': success_count / 100,
        'avg_reward': float(np.mean(episode_rewards)),
        'avg_steps': float(np.mean(episode_steps)),
        'final_biopsy': pop,
        'causality': causality,
    }
    
    metrics_file = os.path.join(output_dir, 'metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print(f"📈 Saved metrics: {metrics_file}")
    print(f"\n✅ Experiment complete! Results in: {output_dir}")

if __name__ == "__main__":
    try:
        run_experiment()
    except Exception as e:
        print(f"\n❌ EXPERIMENT FAILED: {e}")
        import traceback
        traceback.print_exc()
