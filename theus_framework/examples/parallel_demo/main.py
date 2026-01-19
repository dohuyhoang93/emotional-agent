
import asyncio
import os
import sys
import time
import numpy as np
from multiprocessing import shared_memory

# 1. Config Environment
# Force Process Backend (Required for proper NumPy support on current env)
os.environ["THEUS_USE_PROCESSES"] = "1"

# Ensure tasks module is findable
sys.path.append(os.path.dirname(__file__))

from theus import TheusEngine
from theus.context import ShmArray
from tasks import apply_filter

async def main():
    print("=== Theus V3 Parallel API Demo ===")
    
    # 2. Setup Data (Producer)
    # Simulator: Create a 100MB Image (5000x5000 float32)
    SHAPE = (5000, 5000)
    BYTES = 5000 * 5000 * 4 # ~100 MB
    print(f"[*] Allocating {BYTES / 1024 / 1024:.2f} MB Shared Memory...")
    
    shm = shared_memory.SharedMemory(create=True, size=BYTES)
    try:
        # Create Zero-Copy Array
        # Note: We use ShmArray (Theus wrapper) to ensure smart pickling
        raw_arr = np.ndarray(SHAPE, dtype=np.float32, buffer=shm.buf)
        arr = ShmArray(raw_arr, shm=shm)
        arr[:] = np.random.rand(*SHAPE) # Random noise
        arr.shm = shm # Keep reference alive
        
        # 3. Initialize Engine
        class AppContext:
            def __init__(self):
                self.domain = {} # Standard audit log
                self.heavy = {}  # Zero-Copy zone
        
        engine = TheusEngine(context=AppContext())
        
        # 4. Inject Data into Engine (Zero-Copy)
        # Using CAS to update state transactionally
        print("[*] Injecting data into Heavy Zone...")
        engine.compare_and_swap(engine.state.version, heavy={'image': arr})
        
        # 5. Register & Execute Task
        engine.register(apply_filter)
        
        print("[*] Executing Parallel Task...")
        start = time.time()
        
        # Pass lightweight input (kernel size)
        # The 'image' is accessed implicitly via ctx.heavy
        result = await engine.execute(apply_filter, input_data={'kernel_size': 2})
        
        elapsed = time.time() - start
        print(f"[+] Task Completed in {elapsed:.4f}s")
        print(f"    Result Metadata: {result}")
        print(f"    (Worker PID: {result.get('pid')})")
        
    finally:
        # Cleanup
        shm.close()
        shm.unlink()
        print("[*] Cleaned up Shared Memory.")

if __name__ == "__main__":
    asyncio.run(main())
