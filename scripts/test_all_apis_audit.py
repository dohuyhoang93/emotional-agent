
import asyncio
import os
import time
import yaml
import numpy as np
from theus import TheusEngine, process
from theus.contracts import SemanticType
from theus.structures import StateUpdate, ManagedAllocator
from theus.context import BaseSystemContext, BaseDomainContext, BaseGlobalContext

# --- Models ---
class MyDomain(BaseDomainContext):
    def __init__(self):
        self.counter = 0
        self.items = []

class MySystemContext(BaseSystemContext):
    def __init__(self):
        self.global_ctx = BaseGlobalContext()
        self.domain = MyDomain()
    def to_dict(self):
        return {"domain": {"counter": self.domain.counter, "items": self.domain.items}}

# --- Processes ---
from audit_processes import (
    async_inc, 
    sync_inc, 
    parallel_append, 
    pure_violation, 
    test_errors_metadata
)

# --- Tests ---

async def audit_execute_sync_async():
    print("\n--- AUDIT: engine.execute (Async vs Sync) ---")
    engine = TheusEngine(MySystemContext())
    engine.register(async_inc)
    engine.register(sync_inc)
    
    # Verify execute returns coroutine for async_inc
    res_async = await engine.execute("async_inc")
    print(f"Async Execute Result: {res_async} (Expected: 1)")
    
    # Verify execute works for sync_inc
    res_sync = await engine.execute("sync_inc")
    print(f"Sync Execute Result: {res_sync} (Expected: 2)")

async def audit_workflow_sync():
    print("\n--- AUDIT: engine.execute_workflow (Synchronicity) ---")
    engine = TheusEngine(MySystemContext())
    engine.register(sync_inc)
    
    wf_path = "test_wf.yaml"
    with open(wf_path, "w") as f:
        f.write("steps:\n  - process: sync_inc")
    
    try:
        # Wrap in to_thread because it's sync and we are in an event loop
        res = await asyncio.to_thread(engine.execute_workflow, wf_path)
        print(f"Workflow Executed via to_thread: Result={res}")
    except Exception as e:
        print(f"Workflow Execution Failed: {e}")
    finally:
        if os.path.exists(wf_path): os.remove(wf_path)

async def audit_parallel_execution():
    print("\n--- AUDIT: engine.execute_parallel ---")
    engine = TheusEngine(MySystemContext())
    engine.register(parallel_append)
    
    # execute_parallel is sync. But usually we call it via engine.execute which handles the loop.
    print("Testing parallel append...")
    start = time.time()
    # Note: execute_parallel is called inside engine.execute if parallel=True
    await engine.execute("parallel_append", item="Apple")
    print(f"Parallel Task Finished in {time.time() - start:.4f}s")
    print(f"Items: {engine.state.domain.items}")

async def audit_contract_enforcement():
    print("\n--- AUDIT: Contract Enforcement (PURE) ---")
    engine = TheusEngine(MySystemContext())
    engine.register(pure_violation)
    
    try:
        await engine.execute("pure_violation")
        print("FAIL: PURE violation was NOT caught!")
    except Exception as e:
        print(f"SUCCESS: PURE violation caught: {e}")

async def audit_state_update_fields():
    print("\n--- AUDIT: StateUpdate Fields ---")
    # Verified fields from source: key, val, data, heavy, signal, assert_version
    su = StateUpdate(key="domain.counter", val=100, heavy={"test": "ok"}, signal={"go": True})
    print(f"StateUpdate fields supported: {list(su.__dict__.keys())}")
    if "heavy" in su.__dict__ and "signal" in su.__dict__:
        print("SUCCESS: StateUpdate supports 'heavy' and 'signal'.")
    else:
        print("FAIL: StateUpdate missing fields.")

async def audit_heavy_alloc():
    print("\n--- AUDIT: engine.heavy.alloc ---")
    engine = TheusEngine(MySystemContext())
    
    # ManagedAllocator.alloc(self, name, shape, dtype)
    try:
        arr = engine.heavy.alloc("test_shm", shape=(10,), dtype='float32')
        print(f"Allocated Heavy Array: type={type(arr)}, shape={arr.shape}")
        arr[0] = 3.14
        print(f"Data Write/Read Check: {arr[0]}")
    except Exception as e:
        print(f"Heavy Allocation Failed: {e}")

if __name__ == "__main__":
    async def main():
        await audit_execute_sync_async()
        await audit_workflow_sync()
        await audit_parallel_execution()
        await audit_contract_enforcement()
        await audit_state_update_fields()
        await audit_heavy_alloc()
    
    asyncio.run(main())
