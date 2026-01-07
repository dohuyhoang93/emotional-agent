
import sys
from types import SimpleNamespace
try:
    from theus_core import Engine, TrackedDict, Transaction
except ImportError:
    print("CRITICAL: theus_core not found.")
    sys.exit(1)

def test_dict_methods():
    print("\n--- Test Dict Methods (get/update) ---")
    
    # Setup
    py_dict = {"a": 1, "b": 2}
    tx = Transaction()
    tracked = TrackedDict(py_dict, tx, "root")
    
    # 1. Test .get()
    val = tracked.get("a")
    print(f"get('a') = {val}")
    assert val == 1
    
    val_default = tracked.get("z", 99)
    print(f"get('z', 99) = {val_default}")
    assert val_default == 99
    
    # 2. Test .update()
    print("Updating with {'c': 3}...")
    tracked.update({"c": 3})
    print(f"New val for 'c': {tracked.get('c')}")
    assert tracked.get("c") == 3
    
    # Verify Transaction Log
    # Should see SET root.c or similar.
    # We can't easily inspect internal Rust tx log from Python unless exposed.
    # But if update worked, data is there.
    
    print("✅ Dict Methods Verified")

if __name__ == "__main__":
    test_dict_methods()
