"""
Test Manual Process Registration
==================================
Test manual registration thay vì auto-discovery.
"""
import sys
sys.path.append('.')

from theus import TheusEngine
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.processes.snn_rl_bridge import (
    encode_state_to_spikes,
    encode_emotion_vector,
    compute_intrinsic_reward_snn
)
from src.processes.rl_processes import (
    select_action_gated,
    update_q_learning
)


def test_manual_registration():
    """Test manual process registration."""
    print("=" * 60)
    print("Test Manual Process Registration")
    print("=" * 60)
    
    # Create contexts
    global_ctx = GlobalContext(
        initial_needs=[0.5, 0.5],
        initial_emotions=[0.0, 0.0],
        total_episodes=1,
        max_steps=10,
        seed=42,
        switch_locations={},
        initial_exploration_rate=1.0
    )
    
    domain_ctx = DomainContext()
    ctx = SystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)
    
    # Create engine
    engine = TheusEngine(ctx, strict_mode=True)
    
    # Manual register
    print("\n1. Manually registering processes...")
    try:
        engine.register_process('encode_state_to_spikes', encode_state_to_spikes)
        engine.register_process('encode_emotion_vector', encode_emotion_vector)
        engine.register_process('compute_intrinsic_reward_snn', compute_intrinsic_reward_snn)
        engine.register_process('select_action_gated', select_action_gated)
        engine.register_process('update_q_learning', update_q_learning)
        print("   ✅ Manual registration successful")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_manual_registration()
