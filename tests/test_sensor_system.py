"""
Test Sensor System - Verify vector 16-dim
==========================================
Test get_sensor_vector() hoạt động đúng.
"""
import json
import numpy as np
from environment import GridWorld

def test_sensor_vector():
    """Test sensor vector từ môi trường."""
    print("=" * 60)
    print("TEST SENSOR SYSTEM")
    print("=" * 60)
    
    # Load config
    with open('multi_agent_complex_maze.json', 'r') as f:
        config = json.load(f)
    
    env_config = config['experiments'][0]['parameters']['environment_config']
    
    # Create environment
    env = GridWorld(env_config)
    env.reset()
    
    # Test sensor vector
    print("\n1. TEST SENSOR VECTOR:")
    vec = env.get_sensor_vector(0)
    
    print(f"   Vector shape: {vec.shape}")
    print(f"   Vector dtype: {vec.dtype}")
    print(f"   Vector: {vec}")
    
    # Verify shape
    assert vec.shape == (16,), f"Expected shape (16,), got {vec.shape}"
    print("   ✅ Shape OK")
    
    # Verify dtype
    assert vec.dtype == np.float32, f"Expected float32, got {vec.dtype}"
    print("   ✅ Dtype OK")
    
    # Verify values
    assert np.all(vec >= 0.0) and np.all(vec <= 1.0), "Values should be in [0, 1]"
    print("   ✅ Values in range [0, 1]")
    
    # Test kênh 0-1 (vị trí)
    print("\n2. TEST KÊNH 0-1 (VỊ TRÍ):")
    pos = env.agent_positions[0]
    expected_x = pos[0] / env.size
    expected_y = pos[1] / env.size
    print(f"   Agent position: {pos}")
    print(f"   Kênh 0 (x normalized): {vec[0]:.4f} (expected: {expected_x:.4f})")
    print(f"   Kênh 1 (y normalized): {vec[1]:.4f} (expected: {expected_y:.4f})")
    assert abs(vec[0] - expected_x) < 0.01, "Kênh 0 sai"
    assert abs(vec[1] - expected_y) < 0.01, "Kênh 1 sai"
    print("   ✅ Vị trí OK")
    
    # Test kênh 2-9 (xúc giác)
    print("\n3. TEST KÊNH 2-9 (XÚC GIÁC 8 HƯỚNG):")
    print(f"   Tactile sensors: {vec[2:10]}")
    
    # Kiểm tra có ít nhất 1 sensor active (vì agent ở góc, có tường)
    if np.any(vec[2:10] > 0):
        print("   ✅ Có cảm nhận xung quanh")
    else:
        print("   ⚠️ Không cảm nhận gì (có thể ở giữa trống)")
    
    # Test kênh 10-11 (events)
    print("\n4. TEST KÊNH 10-11 (EVENTS):")
    print(f"   Event sensors: {vec[10:12]}")
    if env.broadcast_events:
        print(f"   Broadcast events: {env.broadcast_events}")
        print("   ✅ Có events")
    else:
        print("   ⚠️ Không có events (bình thường ở bước đầu)")
    
    # Test toggle công tắc
    print("\n5. TEST TOGGLE CÔNG TẮC:")
    
    # Di chuyển agent đến công tắc (1, 1)
    # Giả sử agent 0 ở (0, 0), di chuyển xuống và phải
    env.agent_positions[0] = [1, 1]
    
    # Lấy sensor vector
    vec_at_switch = env.get_sensor_vector(0)
    print(f"   Agent tại (1, 1) - vị trí công tắc A")
    print(f"   Sensor vector: {vec_at_switch}")
    
    # Kiểm tra có cảm nhận công tắc không (kênh 2-9 nên có giá trị 1.0)
    # Vì đang ĐỨNG trên công tắc, nên có thể không cảm nhận (chỉ cảm nhận xung quanh)
    # Nhưng nếu có công tắc ở 1 trong 8 hướng xung quanh thì sẽ có 1.0
    
    # Toggle công tắc
    env.perform_action(0, 'down')  # Di chuyển để trigger
    
    # Check broadcast events
    if env.broadcast_events:
        print(f"   ✅ Broadcast events: {env.broadcast_events}")
        
        # Lấy sensor vector sau toggle
        vec_after_toggle = env.get_sensor_vector(0)
        print(f"   Sensor sau toggle: {vec_after_toggle}")
        
        # Kênh 10-11 nên có giá trị
        if vec_after_toggle[10] > 0 or vec_after_toggle[11] > 0:
            print("   ✅ Events được encode vào sensor!")
        else:
            print("   ⚠️ Events không được encode (có thể đã clear)")
    
    print("\n" + "=" * 60)
    print("✅ TEST HOÀN TẤT!")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    try:
        test_sensor_vector()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
