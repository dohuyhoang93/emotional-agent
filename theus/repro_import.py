import sys
import traceback

print("Python executable:", sys.executable)
print("System path:", sys.path)

try:
    print("Attempting to import theus_core...")
    import theus_core
    print("theus_core imported successfully:", theus_core)
except ImportError:
    print("Failed to import theus_core")
    traceback.print_exc()

try:
    print("Attempting to import TheusEngine from theus.engine...")
    from theus.engine import TheusEngine
    print("TheusEngine imported successfully")
except Exception:
    print("Failed to import TheusEngine")
    traceback.print_exc()
