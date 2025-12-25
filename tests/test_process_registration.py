"""
Test Process Registration
==========================
Test xem processes có được register đúng không.
"""
import sys
sys.path.append('.')

from theus import TheusEngine
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.snn_context_theus import SNNGlobalContext, create_snn_context_theus


def test_process_registration():
    """Test process registration."""
    print("=" * 60)
    print("Test Process Registration")
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
    
    domain_ctx = DomainContext(
        N_vector=None,
        E_vector=None
    )
    
    ctx = SystemContext(
        global_ctx=global_ctx,
        domain_ctx=domain_ctx
    )
    
    # Create engine
    engine = TheusEngine(ctx, strict_mode=True)
    
    # Scan and register
    print("\n1. Scanning processes...")
    engine.scan_and_register("src/processes")
    
    # List registered
    print("\n2. Registered processes:")
    if hasattr(engine, '_process_registry'):
        for name in sorted(engine._process_registry.keys()):
            print(f"   - {name}")
    
    print("\n3. Checking specific processes...")
    required = [
        # SNN Core
        'encode_state_to_spikes',
        'process_integrate',
        'process_fire',
        'process_clustering',
        'process_stdp',
        'encode_emotion_vector',
        
        # RL-SNN Bridge
        'compute_intrinsic_reward_snn',
        'combine_rewards',
        'select_action_gated',
        'update_q_learning',
        
        # Legacy (for compatibility)
        'perception',
        'execute_action',
        'record_consequences',
        'social_learning'
    ]
    
    missing = []
    for proc_name in required:
        if hasattr(engine, 'process_registry') and proc_name in engine.process_registry:
            print(f"   ✅ {proc_name}")
        else:
            print(f"   ❌ {proc_name} NOT FOUND")
            missing.append(proc_name)
    
    if missing:
        print(f"\n⚠️  WARNING: {len(missing)} processes missing!")
        print(f"Missing: {missing}")
    else:
        print(f"\n✅ All {len(required)} required processes registered!")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_process_registration()
