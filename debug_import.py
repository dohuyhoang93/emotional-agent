
import sys
import os
sys.path.append(os.getcwd())
sys.path.append('theus')

print("PWD:", os.getcwd())
print("SYS PATH:", sys.path)

try:
    print("Attempting import...")
    from src.orchestrator.processes import p_run_simulations
    print("✅ Import Successful:", p_run_simulations)
except Exception as e:
    print(f"❌ Import Failed: {e}")
    import traceback
    traceback.print_exc()
