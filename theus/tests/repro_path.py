import sys
import os
import traceback
import torch
print("Torch imported")

print("CWD:", os.getcwd())

# Mimic test_core_pop.py path hack
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("Sys.path:", sys.path)

try:
    print("Attempting import theus_core...")
    import theus_core
    print("theus_core imported:", theus_core)
except ImportError:
    print("Failed to import theus_core")
    traceback.print_exc()

try:
    print("Attempting import theus.engine...")
    from theus.engine import TheusEngine
    print("TheusEngine imported.")
except ImportError:
    print("Failed to import TheusEngine")
    traceback.print_exc()
