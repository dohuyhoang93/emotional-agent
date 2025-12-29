
import sys
import os

print(f"CWD: {os.getcwd()}")
print(f"sys.path[0]: {sys.path[0]}")

try:
    import theus
    print(f"theus imported from: {theus}")
    print(f"theus file: {getattr(theus, '__file__', 'None')}")
    print(f"theus path: {getattr(theus, '__path__', 'None')}")
    print(f"dir(theus): {dir(theus)}")
except ImportError as e:
    print(f"ImportError: {e}")

try:
    from theus import TheusEngine
    print("Successfully imported TheusEngine via 'from theus'")
except ImportError as e:
    print(f"Failed 'from theus import TheusEngine': {e}")

try:
    from theus.engine import TheusEngine
    print("Successfully imported TheusEngine via 'from theus.engine'")
except ImportError as e:
    print(f"Failed 'from theus.engine import TheusEngine': {e}")
