
import sys
import os
import numpy as np

print(f"Python: {sys.version}")
print(f"CWD: {os.getcwd()}")

try:
    import theus
    print(f"Theus Version: {theus.__version__}")
    print(f"Theus File: {theus.__file__}")
except ImportError as e:
    print(f"ERROR: Could not import theus: {e}")

try:
    import theus_core
    print("Theus Core (Rust) Version: Loaded Successfully")
    print(f"Theus Core File: {theus_core.__file__}")
except ImportError as e:
    print(f"ERROR: Could not import theus_core: {e}")
    print("WARNING: Running in Mock Mode (Simulated)")

try:
    from theus.engine import TheusEngine
    print("TheusEngine class imported.")
    
    eng = TheusEngine(None)
    print("TheusEngine instantiated.")
except Exception as e:
    print(f"ERROR: Failed to instantiate engine: {e}")
