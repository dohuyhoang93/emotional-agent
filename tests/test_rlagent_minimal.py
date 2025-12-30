"""
Minimal Test - RLAgent với Orchestration
==========================================
Test để debug AttributeError trong encode_state_to_spikes.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')
sys.path.append('theus')

from src.agents.rl_agent import RLAgent
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.snn_context_theus import SNNGlobalContext, create_snn_context_theus
from environment import GridWorld
from src.adapters.environment_adapter import EnvironmentAdapter
from theus import TheusEngine
import torch
import numpy as np
import os

def main():
    print("=" * 70)
    print("MINIMAL RLAGENT TEST")
    print("=" * 70)
    
    # Create contexts
    global_ctx = GlobalContext(
        initial_needs=[0.5, 0.5],
        initial_emotions=[0.0, 0.0],
        total_episodes=1,
        max_steps=5,
        seed=42,
        switch_locations={},
        initial_exploration_rate=1.0
    )
    # Phase 2: Test Centralized Config with custom values
    global_ctx.model_config = {
        "obs_dim": 5,
        "emotion_dim": 16,
        "hidden_dim": 32, # Custom dim to verify injection
        "action_dim": 8,
        "gated_lr": 0.005 # Custom LR
    }
    
    snn_global_ctx = SNNGlobalContext(
        num_neurons=50,
        vector_dim=16,
        connectivity=0.15,
        seed=42
    )
    
    # Create agent
    print("\n1. Creating RLAgent...")
    try:
        # Manual Dependency Injection Setup
        agent_id = 0
        
        # 1. Domain Context
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
            q_table={},
            short_term_memory=[],
            long_term_memory={},
            base_exploration_rate=global_ctx.initial_exploration_rate,
            current_exploration_rate=global_ctx.initial_exploration_rate,
            N_vector=torch.tensor([0.5, 0.5]),
            E_vector=torch.tensor([0.0]*16)
        )
        
        # 2. SNN Context
        snn_ctx = create_snn_context_theus(
            num_neurons=50,
            connectivity=0.15,
            vector_dim=16,
            seed=42
        )
        domain_ctx.snn_context = snn_ctx
        
        # 3. System Context
        rl_ctx = SystemContext(
            global_ctx=global_ctx,
            domain_ctx=domain_ctx
        )
        
        # 4. Engine
        engine = TheusEngine(
            rl_ctx,
            strict_mode=True
        )
        # Scan processes (Must point to src/processes)
        # Assuming we are running from root
        processes_dir = os.path.abspath("src/processes")
        engine.scan_and_register(processes_dir)

        # 5. Agent
        agent = RLAgent(
            rl_ctx=rl_ctx,
            engine=engine
        )
        print("✅ Agent created")
        
        # Verify Config Injection
        assert agent.gated_network.hidden_dim == 32, "Hidden Dim should be 32 (from config)"
        assert agent.gated_network.obs_encoder[0].out_features == 32, "Encoder Out Dim should be 32"
        assert agent.optimizer.param_groups[0]['lr'] == 0.005, "LR should be 0.005 (from config)"
        print("✅ Config Injection Verified (Validating Phase 2)")
    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Create environment
    print("\n2. Creating Environment...")
    env_config = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 8,
            "max_steps_per_episode": 5,
            "num_agents": 1,
            "start_positions": [[0, 0]]
        }
    }
    env = GridWorld(env_config)
    adapter = EnvironmentAdapter(env)
    print("✅ Environment created")
    
    # Reset
    print("\n3. Resetting...")
    obs_dict = env.reset()
    agent.reset(obs_dict[0])
    print(f"✅ Reset complete. Observation: {obs_dict[0]}")
    
    # Take one step
    print("\n4. Taking one step...")
    try:
        action = agent.step(adapter)
        print(f"✅ Step complete. Action: {action}")
    except Exception as e:
        print(f"❌ Step failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
