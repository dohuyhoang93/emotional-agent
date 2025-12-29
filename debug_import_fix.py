
import sys
import os

print(f"Original sys.path[0]: {sys.path[0]}")

# HACK: Move CWD to end of path to prefer installed packages over local folders
if sys.path[0] == os.getcwd() or sys.path[0] == '':
    cwd = sys.path.pop(0)
    sys.path.append(cwd)

print(f"Modified sys.path[0]: {sys.path[0]}")

try:
    import theus
    print(f"theus imported from: {theus}")
    print(f"theus file: {getattr(theus, '__file__', 'None')}")
except ImportError as e:
    print(f"ImportError theus: {e}")

try:
    from theus import TheusEngine
    print("Successfully imported TheusEngine via 'from theus'")
except ImportError as e:
    print(f"Failed 'from theus import TheusEngine': {e}")

try:
    import src
    print(f"src imported from: {src}")
except ImportError as e:
    print(f"ImportError src: {e}")
