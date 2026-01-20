

import asyncio
import os
import sys
import time
import numpy as np

# 1. Config Environment
os.environ["THEUS_USE_PROCESSES"] = "1"
sys.path.append(os.path.dirname(__file__))

from theus import TheusEngine
from tasks import process_partition

async def main():
    print("=== Theus V3 Complex Parallel Demo (Managed Memory) ===")
    
    # 2. Initialize Engine First (Allocator is here)
    engine = TheusEngine()
    
    # 3. Setup Data (Producer)
    SIZE = 20_000_000 
    
    # NEW API: Alloc 160MB Managed Memory
    # No explicit SharedMemory import needed!
    print(f"[*] Allocating Managed Memory for {SIZE} floats...")
    arr_in = engine.heavy.alloc("source_data", shape=(SIZE,), dtype=np.float32)
    arr_out = engine.heavy.alloc("results_data", shape=(SIZE,), dtype=np.float32)
    
    # Populate Input
    print(f"[*] generating random floats...")
    arr_in[:] = np.random.rand(SIZE)
    
    # Inject Data (Zero-Copy)
    # Note: arr_in IS a ShmArray, so it works directly
    engine.compare_and_swap(engine.state.version, heavy={
        'source_data': arr_in,
        'results_data': arr_out
    })
    
    try:
        # 4. Dispatch Parallel Tasks (Partitioning)
        NUM_WORKERS = 4
        chunk_size = SIZE // NUM_WORKERS
        tasks = []
        
        print(f"[*] Dispatching {NUM_WORKERS} workers (Chunk size: {chunk_size})...")
        
        start_time = time.time()
        
        # Register Process
        engine.register(process_partition)
        
        for i in range(NUM_WORKERS):
            start_idx = i * chunk_size
            end_idx = start_idx + chunk_size
            
            coro = engine.execute(process_partition, 
                partition_id=i,
                start_idx=start_idx,
                end_idx=end_idx
            )
            tasks.append(coro)
            
        # Wait for all
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        print(f"[+] All workers finished in {elapsed:.4f}s")
        
        # 5. Aggregate Deltas
        total_sum = 0.0
        total_rows = 0
        pids = set()
        
        for res in results:
            if isinstance(res, Exception):
                print(f"[-] Worker Failed: {res}")
            else:
                total_sum += res['partial_sum']
                total_rows += res['rows_processed']
                pids.add(res['pid'])
                print(f"    Worker {res['p_id']}: Sum={res['partial_sum']:.2f}")

        # 6. Verify Correctness
        print("[*] Verifying result consistency...")
        expected_sum = np.sum(np.power(arr_in, 2))
        
        is_correct = np.isclose(total_sum, expected_sum, rtol=1e-5)
        
        print("\n=== Verification Report ===")
        print(f"Workers Used: {len(pids)} (PIDs: {pids})")
        print(f"Rows Processed: {total_rows}/{SIZE}")
        print(f"Total Sum (Parallel): {total_sum:.4f}")
        print(f"Consensus: {'✅ MATCH' if is_correct else '❌ MISMATCH'}")
        
    finally:
        # No more manual unlink!
        pass

if __name__ == "__main__":
    asyncio.run(main())
