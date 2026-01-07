import sys
from typing import Any
try:
    from theus_core import Transaction, TrackedList, TrackedDict
except ImportError:
    print("CRITICAL: theus_core not found or struct missing.")
    sys.exit(1)

def test_structures():
    print("\n--- Test Structures ---")
    tx = Transaction()
    
    # List
    data = [1, 2, 3]
    tl = TrackedList(data, tx, "test_list")
    print(f"TrackedList: {tl}")
    
    tl.append(4)
    print(f"Appended 4: {data}")
    assert data == [1, 2, 3, 4]
    
    # Dict
    d = {"a": 1}
    td = TrackedDict(d, tx, "test_dict")
    print(f"TrackedDict: {td}")
    
    td["b"] = 2
    print(f"Set b=2: {d}")
    assert d == {"a": 1, "b": 2}

    print("✅ Structures Basic Test Passed")

if __name__ == "__main__":
    test_structures()
