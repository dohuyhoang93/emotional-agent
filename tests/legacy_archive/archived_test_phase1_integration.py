"""
Phase 1 Integration Tests
==========================
Test RLAgent với SNN-RL integration.
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

def create_test_environment():
    """Tạo GridWorld environment."""
    settings = {
        "initial_needs": [0.5, 0.5],
        "initial_emotions": [0.0, 0.0],
        "switch_locations": {},
        "environment_config": {
            "grid_size": 10,
            "max_steps_per_episode": 100,
            "num_agents": 1
        }
    }
    return GridWorld(settings)


def test_rl_agent_creation():
    """Test RLAgent initialization."""
    print("=" * 60)
    print("Test: RLAgent Creation")
    print("=" * 60)
    
    agent, rl_ctx, global_ctx = create_full_test_context_and_agent()
    
    # Validate components
    assert agent.snn_ctx is not None
    assert agent.gated_network is not None
    assert agent.engine is not None
    assert len(agent.snn_ctx.domain_ctx.neurons) == 50
    
    print("  ✅ Agent created")
    print(f"  ✅ SNN neurons: {len(agent.snn_ctx.domain_ctx.neurons)}")
    print("✅ RLAgent creation works!")


def test_single_step():
    """Test single step execution."""
    print("\n" + "=" * 60)
    print("Test: Single Step")
    print("=" * 60)
    
    agent, rl_ctx, global_ctx = create_full_test_context_and_agent()
    
    env = create_test_environment()
    adapter = EnvironmentAdapter(env)
    
    # Reset
    obs_dict = env.reset()
    agent.reset(obs_dict[0])
    
    print(f"  Initial observation: {obs_dict[0]['agent_pos']}")
    
    # Step 
    try:
        action = agent.step(adapter)
        
        # Validate
        assert action in range(8) # Action dim is 8 in config
        print(f"  ✅ Action selected: {action}")
        
        # Check SNN was used
        metrics = agent.get_metrics()
        print(f"  ✅ SNN fire rate: {metrics['snn'].get('fire_rate', 0):.4f}")
        print(f"  ✅ Intrinsic reward: {agent.domain_ctx.intrinsic_reward:.4f}")
        
        # Position is tracked in domain_ctx directly
        print(f"  ✅ Position: {agent.domain_ctx.position}")
    except Exception as e:
        print(f"  ⚠️ Step failed (check processes dir): {e}")
        import traceback
        traceback.print_exc()
        raise e


def test_agent_reset():
    """Test agent reset functionality."""
    print("\n" + "=" * 60)
    print("Test: Agent Reset")
    print("=" * 60)
    
    agent, rl_ctx, global_ctx = create_full_test_context_and_agent()
    
    env = create_test_environment()
    obs_dict = env.reset()
    
    # Reset agent
    agent.reset(obs_dict[0])
    
    # Validate reset
    assert agent.domain_ctx.current_step == 0
    assert agent.snn_ctx.domain_ctx.current_time == 0
    # ensure_heavy_tensors_initialized might have populated heavy tensors, check object state?
    # Objects might drift if not synced. But reset should zero things.
    
    print("  ✅ SNN state reset")
    print("✅ Agent reset works!")


def test_gated_network():
    """Test Gated Integration Network."""
    print("\n" + "=" * 60)
    print("Test: Gated Integration Network")
    print("=" * 60)
    
    agent, rl_ctx, global_ctx = create_full_test_context_and_agent()
    
    # Create dummy inputs
    obs = torch.randn(1, global_ctx.model_config['obs_dim']) 
    emotion = torch.randn(1, global_ctx.model_config['emotion_dim']) 
    
    # Forward pass
    with torch.no_grad():
        q_values = agent.gated_network(obs, emotion)
    
    # Validate
    expected_dim = global_ctx.model_config['action_dim']
    # Ensure shape match (handle 1D return if unbatched)
    if q_values.dim() == 1:
        q_values = q_values.unsqueeze(0)
        
    assert q_values.shape == (1, expected_dim) 
    
    print(f"  ✅ Input shapes: obs={obs.shape}, emotion={emotion.shape}")
    print(f"  ✅ Output shape: {q_values.shape}")
    print("✅ Gated network works!")


def test_metrics_tracking():
    """Test metrics tracking."""
    print("\n" + "=" * 60)
    print("Test: Metrics Tracking")
    print("=" * 60)
    
    agent, rl_ctx, global_ctx = create_full_test_context_and_agent()
    
    # Get metrics
    metrics = agent.get_metrics()
    
    # Validate structure
    assert 'rl' in metrics
    assert 'snn' in metrics
    
    print(f"  ✅ RL metrics: {list(metrics['rl'].keys())}")
    print(f"  ✅ SNN metrics: {list(metrics['snn'].keys())}")
    print("✅ Metrics tracking works!")


if __name__ == '__main__':
    # Run tests
    test_rl_agent_creation()
    test_agent_reset()
    test_gated_network()
    test_metrics_tracking()
    test_single_step()
    
    print("\n" + "=" * 60)
    print("✅ PHASE 1 INTEGRATION TESTS COMPLETE!")
    print("=" * 60)
