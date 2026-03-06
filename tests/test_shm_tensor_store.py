"""
Test ShmTensorStore
===================
Unit tests cho ShmTensorStore: alloc, read, write, fallback mode.
"""
import sys
import numpy as np

sys.path.append('.')

from src.utils.shm_tensor_store import ShmTensorStore


def test_fallback_mode():
    """ShmTensorStore hoạt động như dict bình thường khi không có allocator."""
    print("Test: Fallback Mode (no allocator)")
    store = ShmTensorStore(allocator=None, prefix="test")

    arr = np.ones((10, 10), dtype=np.float32)
    store['weights'] = arr

    assert 'weights' in store
    assert store['weights'].shape == (10, 10)
    assert np.allclose(store['weights'], 1.0)
    print("  ✅ Fallback mode works (plain dict)")


def test_shm_mode():
    """ShmTensorStore cấp SharedMemory qua HeavyZoneAllocator."""
    print("\nTest: SHM Mode (with allocator)")
    try:
        from theus.context import HeavyZoneAllocator
        allocator = HeavyZoneAllocator()
    except Exception as e:
        print(f"  ⚠️ HeavyZoneAllocator unavailable, skipping: {e}")
        return

    store = ShmTensorStore(allocator=allocator, prefix="test_shm")

    # Alloc mới
    arr = np.random.rand(100, 100).astype(np.float32)
    store['weights'] = arr
    assert 'weights' in store
    assert store['weights'].shape == (100, 100)
    assert np.allclose(store['weights'], arr)
    print("  ✅ SHM alloc + read works")

    # Overwrite in-place (same shape)
    arr2 = np.zeros((100, 100), dtype=np.float32)
    store['weights'] = arr2
    assert np.allclose(store['weights'], 0.0)
    print("  ✅ In-place overwrite works")

    # Non-ndarray value (bool flag)
    store['use_vectorized_queue'] = True
    assert store['use_vectorized_queue'] is True
    print("  ✅ Non-ndarray values stored in plain dict")

    # Get with default
    assert store.get('nonexistent', 42) == 42
    print("  ✅ .get() with default works")

    # Repr
    print(f"  repr: {store!r}")

    # Cleanup
    allocator.cleanup()
    print("  ✅ Cleanup done")


def test_multiple_agents():
    """Simulate multi-agent SHM allocation."""
    print("\nTest: Multi-agent SHM allocation")
    try:
        from theus.context import HeavyZoneAllocator
        allocator = HeavyZoneAllocator()
    except Exception as e:
        print(f"  ⚠️ HeavyZoneAllocator unavailable, skipping: {e}")
        return

    stores = []
    for i in range(3):
        store = ShmTensorStore(allocator=allocator, prefix=f"agent_{i}")
        store['potentials'] = np.zeros(50, dtype=np.float32)
        store['weights'] = np.random.rand(50, 50).astype(np.float32)
        stores.append(store)

    # Verify isolation
    stores[0]['potentials'][:] = 1.0
    assert np.allclose(stores[0]['potentials'], 1.0)
    assert np.allclose(stores[1]['potentials'], 0.0), "Agent 1 should not be affected"
    print("  ✅ Agent isolation preserved")

    # Verify all have unique SHM segments
    assert len(allocator._allocations) >= 6, f"Expected >=6 allocations, got {len(allocator._allocations)}"
    print(f"  ✅ {len(allocator._allocations)} SHM segments allocated across 3 agents")

    allocator.cleanup()
    print("  ✅ Cleanup done")


if __name__ == '__main__':
    test_fallback_mode()
    test_shm_mode()
    test_multiple_agents()

    print("\n" + "=" * 60)
    print("✅ ALL ShmTensorStore TESTS PASSED!")
    print("=" * 60)
