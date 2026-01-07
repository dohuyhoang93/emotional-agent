
import sys
from types import SimpleNamespace
try:
    from theus_core import ContextGuard, TrackedList, FrozenList
except ImportError:
    print("CRITICAL: theus_core not found.")
    sys.exit(1)

def test_guards_integration():
    print("\n--- Test Guards Integration ---")
    
    # Setup Data (Dict)
    target = {
        "data": [1, 2, 3],
        "config": [10, 20]
    }
    
    # Setup Guard: 'data' is output (Writeable), 'config' is input (Read Only)
    guard = ContextGuard(target, ["config"], ["data"])
    
    print(f"Guard created: {guard}")
    
    # 1. Test Writeable Path (data) -> TrackedList
    print("Accessing 'data' (Writeable) via Item Access...")
    d = guard['data']
    print(f"Type of guard['data']: {type(d)}")
    assert isinstance(d, TrackedList), f"Expected TrackedList for 'data', got {type(d)}"
    
    # Mutate
    d.append(4)
    print(f"Appended 4 to data: {d}")
    # Verify shadow update
    # Note: d is the wrapper around the shadow list.
    assert str(d) == "[1, 2, 3, 4]"

    # 2. Test Read-Only Path (config) -> FrozenList
    print("Accessing 'config' (Read-Only) via Item Access...")
    c = guard['config']
    print(f"Type of guard['config']: {type(c)}")
    assert isinstance(c, FrozenList), f"Expected FrozenList for 'config', got {type(c)}"
    
    # Attempt Mutate
    try:
        c.append(30)
        print("CRITICAL: FrozenList allowed append!")
        sys.exit(1)
    except TypeError as e:
        print(f"✅ Caught expected TypeError: {e}")

    # 3. Test Object Attribute Access
    print("\n--- Test Object Attribute Access ---")
    obj_target = SimpleNamespace(data=[1, 2], config=[10])
    guard_obj = ContextGuard(obj_target, ["config"], ["data"])
    
    d_obj = guard_obj.data
    assert isinstance(d_obj, TrackedList)
    print("✅ Dot access for Writeable Object passed")
    
    c_obj = guard_obj.config
    assert isinstance(c_obj, FrozenList)
    print("✅ Dot access for Read-Only Object passed")
        
    print("✅ All Guards Integration Tests Passed")

if __name__ == "__main__":
    test_guards_integration()
