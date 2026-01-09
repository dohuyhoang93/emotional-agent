"""
Simple End-to-End Test
=======================
Test đơn giản nhất để validate Phase 1 integration.
Updated to use correct TheusEngine injection.
"""
import sys
import os
import torch
import numpy as np
import pytest

sys.path.append('.')
sys.path.append('theus')

from src.agents.rl_agent import RLAgent
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.snn_context_theus import SNNGlobalContext, create_snn_context_theus
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld
from theus import TheusEngine

def create_full_test_context_and_agent(agent_id=0):
    """Helper to create a fully wired agent + engine + context."""
    # 1. Global Setup
    global_ctx = GlobalContext(
        initial_needs=[0.5, 0.5],
        initial_emotions=[0.0, 0.0],
        total_episodes=1,
        max_steps=100,
        seed=42,
        switch_locations={},
        initial_exploration_rate=0.5
    )
    # Phase 2: Test Centralized Config with custom values
    global_ctx.model_config = {
        "obs_dim": 5,
        "emotion_dim": 16,
        "hidden_dim": 32, 
        "action_dim": 8,
        "gated_lr": 0.005
    }

    # 2. Domain Context
    domain_ctx = DomainContext(
        agent_id=agent_id,
        position=[0, 0],
        has_key=False,
        is_at_goal=False,
        last_action=-1,
        last_reward={'extrinsic': 0.0, 'intrinsic': 0.0},
        current_observation=None,
        emotion_state=np.zeros(16, dtype=np.float32),
        believed_switch_states={},
        heavy_q_table={},
        short_term_memory=[],
        long_term_memory={},
        base_exploration_rate=global_ctx.initial_exploration_rate,
        current_exploration_rate=global_ctx.initial_exploration_rate,
        N_vector=torch.tensor([0.5, 0.5]),
        heavy_E_vector=torch.tensor([0.0]*16)
    )
    
    # 3. SNN Context
    snn_ctx = create_snn_context_theus(
        num_neurons=50,
        connectivity=0.15,
        vector_dim=16,
        seed=42
    )
    domain_ctx.snn_context = snn_ctx
    
    # 4. System Context
    rl_ctx = SystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )
    
    # 5. Engine
    engine = TheusEngine(
        rl_ctx,
        strict_mode=True
    )
    processes_dir = os.path.abspath("src/processes")
    engine.scan_and_register(processes_dir)
    
    # 6. Agent
    agent = RLAgent(
        rl_ctx=rl_ctx,
        engine=engine
    )
    
    return agent, rl_ctx, global_ctx

def test_simple_episode():
    """Test simple episode với RLAgent."""
    print("=" * 60)
    print("Simple End-to-End Test")
    print("=" * 60)
    
    # Create agent
    print("Creating agent...")
    agent, rl_ctx, global_ctx = create_full_test_context_and_agent()
    print(f"  ✅ Agent created with {len(agent.snn_ctx.domain_ctx.neurons)} neurons")
    
    # Create environment
    settings = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 5,  # Small grid
            "max_steps_per_episode": 10,
            "num_agents": 1
        }
    }
    env = GridWorld(settings)
    adapter = EnvironmentAdapter(env)
    
    # Reset
    print("\nResetting environment...")
    obs_dict = env.reset()
    agent.reset(obs_dict[0])
    print(f"  ✅ Initial position: {obs_dict[0]['agent_pos']}")
    
    # Run episode
    print("\nRunning episode (10 steps max)...")
    total_reward = 0
    
    for step in range(10):
        print(f"\n  Step {step + 1}:")
        
        try:
            # Step
            action = agent.step(adapter)
            
            # Get metrics
            metrics = agent.get_metrics()
            
            # Safely access metrics with defaults
            fire_rate = metrics.get('snn', {}).get('fire_rate', 0.0)
            active_synapses = metrics.get('snn', {}).get('active_synapses', 0)
            
            print(f"    Action: {action}")
            print(f"    Position: {agent.domain_ctx.position}")
            print(f"    SNN fire rate: {fire_rate:.4f}")
            
            # Helper to sum rewards
            last_rw = agent.domain_ctx.last_reward
            if isinstance(last_rw, dict):
                 reward_val = last_rw.get('total', 0.0)
            else:
                 reward_val = float(last_rw) if last_rw is not None else 0.0

            total_reward += reward_val
            
            # Check done
            if env.is_done():
                print(f"\n  ✅ Episode done at step {step + 1}!")
                break
                
        except Exception as e:
            print(f"\n  ❌ Error at step {step + 1}: {e}")
            print("  This is expected if workflow processes not all registered (e.g. imports failed)")
            # Should fail test if exception occurs
            raise e
    
    # Summary
    print("\n" + "=" * 60)
    print("Episode Summary")
    print("=" * 60)
    print(f"  Total reward: {total_reward:.4f}")
    print(f"  Steps: {agent.episode_metrics['steps']}")
    
    print("\n✅ END-TO-END TEST PASSED!")


if __name__ == '__main__':
    test_simple_episode()
