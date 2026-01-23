"""
THEUS ARCHITECTURE BENCHMARK
============================
Comparing:
A. Current Architecture (Owner Model)     -> Serialization Cost
B. Supervisor Architecture (Manager Model)-> GIL/Lock Cost

Goal: Determine if 'Zero-Copy' reads outweigh 'GIL-Bound' writes.
"""
import time
import threading
import sys
import os
import secrets
from concurrent.futures import ThreadPoolExecutor

# Ensure local import
sys.path.insert(0, os.path.abspath("."))

from theus.context import BaseSystemContext, BaseDomainContext, BaseGlobalContext
from dataclasses import dataclass, field
from theus import TheusEngine
from theus.prototype.supervisor import SupervisorEngine

# --- SETUP ---
DATA_SIZE = 1000 # Elements in list
ITERATIONS = 50000

# Large Data Object (to punish serialization)
def make_large_data():
    return {"key": "val", "list": [secrets.token_hex(16) for _ in range(DATA_SIZE)]}

large_data = make_large_data()

# 1. Setup Standard Engine
@dataclass
class MyDomain(BaseDomainContext):
    data: dict = field(default_factory=make_large_data)

@dataclass
class MyGlobal(BaseGlobalContext):
    pass

@dataclass
class MyContext(BaseSystemContext):
    pass

domain = MyDomain()
gl = MyGlobal()
ctx = MyContext(global_ctx=gl, domain=domain)
engine_owner = TheusEngine(context=ctx)

# 2. Setup Supervisor Engine
engine_sup = SupervisorEngine(init_data={"domain": {"data": large_data}})


# --- BENCHMARKS ---

def bench_read_owner(eng, label):
    start = time.time()
    for _ in range(ITERATIONS):
        # Access triggers Deep Copy (Serialization + Deserialization)
        _ = eng.state.domain['data']
    end = time.time()
    print(f"[{label}] Read: {ITERATIONS} ops in {end-start:.4f}s => {ITERATIONS/(end-start):.0f} ops/s")

def bench_read_supervisor(eng, label):
    start = time.time()
    for _ in range(ITERATIONS):
        # Access is Zero Copy (Pointer Return)
        _ = eng.read("domain")['data']
    end = time.time()
    print(f"[{label}] Read: {ITERATIONS} ops in {end-start:.4f}s => {ITERATIONS/(end-start):.0f} ops/s")

def bench_write_owner(eng, label):
    # Single Thread Write
    start = time.time()
    ver = 0
    updates = {"domain": {"counter": 0}}
    for i in range(ITERATIONS // 10): # Writes are slower
        # CAS Cost: Serialize Update -> Send to Rust -> Update -> Return
        # Note: version is simplified here
        eng.compare_and_swap(ver, updates)
        ver += 1
    end = time.time()
    # Note: Reduced iterations for write to finish in reasonable time
    ops = ITERATIONS // 10
    print(f"[{label}] Write: {ops} ops in {end-start:.4f}s => {ops/(end-start):.0f} ops/s")

def bench_write_supervisor(eng, label):
    # Single Thread Write
    start = time.time()
    ver = 0
    for i in range(ITERATIONS // 10):
        # CAS Cost: Lock -> Check -> Update Ptr
        eng.compare_and_swap("domain", ver, {"data": "new"})
        ver += 1
    end = time.time()
    ops = ITERATIONS // 10
    print(f"[{label}] Write: {ops} ops in {end-start:.4f}s => {ops/(end-start):.0f} ops/s")

def run_bench():
    print(f"BENCHMARK CONFIG: DataSize={DATA_SIZE}, Iterations={ITERATIONS}")
    print("----------------------------------------------------------------")
    
    # 1. READ TEST (The winner should be Supervisor)
    print("\n--- TEST 1: READ PERFORMANCE ---")
    bench_read_owner(engine_owner, "Owner (Current)")
    bench_read_supervisor(engine_sup, "Supervisor (New)")
    
    # 2. WRITE TEST (Serial)
    print("\n--- TEST 2: WRITE PERFORMANCE (Single Thread) ---")
    # Helper to init extra key for owner so it doesn't crash on 'counter'
    engine_owner.compare_and_swap(0, {"domain": {"counter": 0}})
    
    try:
        bench_write_owner(engine_owner, "Owner (Current)")
    except Exception as e:
        print(f"[Owner] Write Failed: {e}")
        
    bench_write_supervisor(engine_sup, "Supervisor (New)")

    print("\n----------------------------------------------------------------")
    print("ANALYSIS PREDICTION:")
    print("1. Supervisor Reads should be 100x-1000x faster (Zero Copy).")
    print("2. Supervisor Writes might be faster (No Serialize) OR slower (Lock) depending on Payload size.")
    print("----------------------------------------------------------------")

if __name__ == "__main__":
    run_bench()
