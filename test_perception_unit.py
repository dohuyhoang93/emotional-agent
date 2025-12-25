"""
Unit Test - Perception Process
===============================
Test perception process với sensor vector.
"""
import numpy as np
from src.core.context import SystemContext, DomainContext, GlobalContext
from src.adapters.environment_adapter import EnvironmentAdapter
from src.processes.p1_perception import perception
from environment import GridWorld
import json

def test_perception_sensor_vector():
    """Test perception với sensor vector."""
    print("=" * 60)
    print("TEST PERCEPTION - SENSOR VECTOR")
    print("=" * 60)
    
    # Load config
    with open('multi_agent_complex_maze.json', 'r') as f:
        config = json.load(f)
    
    env_config = config['experiments'][0]['parameters']['environment_config']
    
    # Create environment
    env = GridWorld(env_config)
    env.reset()
    
    # Create adapter
    adapter = EnvironmentAdapter(env)
    
    # Create context
    global_ctx = GlobalContext()
    domain_ctx = DomainContext()
    ctx = SystemContext(global_ctx, domain_ctx)
    
    print("\n1. TEST GET SENSOR VECTOR:")
    vec = adapter.get_sensor_vector(0)
    print(f"   Vector shape: {vec.shape}")
    print(f"   Vector type: {type(vec)}")
    assert isinstance(vec, np.ndarray), "Should be numpy array"
    assert vec.shape == (16,), f"Should be (16,), got {vec.shape}"
    print("   ✅ Sensor vector OK")
    
    print("\n2. TEST PERCEPTION PROCESS:")
    # Call perception
    perception(ctx, adapter, agent_id=0)
    
    # Check observation updated
    obs = ctx.domain_ctx.current_observation
    print(f"   Observation type: {type(obs)}")
    print(f"   Observation shape: {obs.shape if isinstance(obs, np.ndarray) else 'N/A'}")
    
    if isinstance(obs, np.ndarray):
        assert obs.shape == (16,), "Should be vector"
        print("   ✅ Perception returns vector")
    else:
        print("   ⚠️ Perception returns dict (legacy mode)")
    
    print("\n3. TEST PREVIOUS OBSERVATION:")
    # Call again
    perception(ctx, adapter, agent_id=0)
    
    prev_obs = ctx.domain_ctx.previous_observation
    curr_obs = ctx.domain_ctx.current_observation
    
    print(f"   Previous obs type: {type(prev_obs)}")
    print(f"   Current obs type: {type(curr_obs)}")
    
    if isinstance(prev_obs, np.ndarray) and isinstance(curr_obs, np.ndarray):
        print("   ✅ Both are vectors")
    
    print("\n" + "=" * 60)
    print("✅ TEST HOÀN TẤT!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_perception_sensor_vector()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
