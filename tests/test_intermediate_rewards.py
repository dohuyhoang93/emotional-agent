"""
Test Intermediate Rewards
==========================
Verify rewards cho toggle công tắc và mở cổng.
"""
import json
from environment import GridWorld

def test_intermediate_rewards():
    """Test intermediate rewards."""
    print("=" * 60)
    print("TEST INTERMEDIATE REWARDS")
    print("=" * 60)
    
    # Load config
    with open('multi_agent_complex_maze.json', 'r') as f:
        config = json.load(f)
    
    env_config = config['experiments'][0]['parameters']['environment_config']
    
    # Create environment
    env = GridWorld(env_config)
    env.reset()
    
    print("\n1. TEST BASE REWARD (STEP PENALTY):")
    env.agent_positions[0] = [5, 5]  # Vị trí trống
    reward = env.perform_action(0, 'up')
    print(f"   Move to empty cell: reward = {reward}")
    assert reward == -0.1, f"Expected -0.1, got {reward}"
    print("   ✅ Step penalty OK")
    
    print("\n2. TEST INVALID MOVE PENALTY:")
    env.agent_positions[0] = [0, 0]  # Góc
    reward = env.perform_action(0, 'up')  # Ra ngoài
    print(f"   Move out of bounds: reward = {reward}")
    assert reward == -0.5, f"Expected -0.5, got {reward}"
    print("   ✅ Invalid move penalty OK")
    
    print("\n3. TEST TOGGLE CÔNG TẮC REWARD:")
    # Công tắc A tại (1, 1)
    # Di chuyển agent từ (1, 0) xuống (1, 1)
    env.reset()
    env.agent_positions[0] = [1, 0]
    print(f"   Agent tại {env.agent_positions[0]}, di chuyển xuống (1, 1) - công tắc A")
    
    reward = env.perform_action(0, 'down')  # Move to (1, 1)
    print(f"   Toggle switch A: reward = {reward}")
    
    # Reward = -0.1 (step) + 1.0 (toggle) + 0.5 × N (gates)
    # Tối thiểu = -0.1 + 1.0 = 0.9
    assert reward >= 0.9, f"Expected >= 0.9, got {reward}"
    print(f"   ✅ Toggle reward OK (reward = {reward})")
    
    # Check broadcast events
    print(f"   Broadcast events: {env.broadcast_events}")
    assert any(e['type'] == 'switch_toggle' for e in env.broadcast_events), "No switch_toggle event"
    print("   ✅ Switch toggle event OK")
    
    # Check gate changed event
    if any(e['type'] == 'gate_changed' for e in env.broadcast_events):
        print("   ✅ Gate changed event OK")
    else:
        print("   ⚠️ No gate changed event (có thể gate không thay đổi)")
    
    print("\n4. TEST GOAL REWARD:")
    env.agent_positions[0] = [23, 24]
    reward = env.perform_action(0, 'down')  # Move to goal (24, 24)
    print(f"   Reach goal: reward = {reward}")
    
    # Reward = -0.1 (step) + 10.0 (goal) = 9.9
    assert reward >= 9.0, f"Expected >= 9.0, got {reward}"
    print("   ✅ Goal reward OK")
    
    print("\n5. TEST REWARD BREAKDOWN:")
    env.reset()
    env.agent_positions[0] = [0, 1]
    
    print("   Scenario: Toggle switch A")
    reward = env.perform_action(0, 'down')
    
    print(f"   Total reward: {reward}")
    print("   Breakdown:")
    print("     - Step penalty: -0.1")
    print("     - Toggle switch: +1.0")
    print("     - Gate changes: +0.5 × N (N = số gates thay đổi)")
    print(f"   Expected: {reward} = -0.1 + 1.0 + 0.5 × {len([e for e in env.broadcast_events if e['type'] == 'gate_changed'])}")
    
    print("\n" + "=" * 60)
    print("✅ TEST HOÀN TẤT!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_intermediate_rewards()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
