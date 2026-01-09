import sys
import os
import psutil
import time
import gc
from dataclasses import dataclass

# Add current directory to path
sys.path.append(os.getcwd())
sys.path.append('theus')

from theus.engine import TheusEngine
from theus.context import BaseSystemContext, BaseGlobalContext, BaseDomainContext

# Minimal Contexts
@dataclass
class MockGlobal(BaseGlobalContext):
    pass

@dataclass
class MockDomain(BaseDomainContext):
    counter: int = 0

@dataclass
class MockSystem(BaseSystemContext):
    global_ctx: MockGlobal
    domain_ctx: MockDomain

# Minimal Workflow
WORKFLOW_YAML = """
name: "Benchmark Loop"
steps:
  - name: "No-op"
    process: "noop_process"
"""

# Create a process file and workflow file
os.makedirs("workflows", exist_ok=True)
with open("workflows/bench_leak.yaml", "w") as f:
    f.write(WORKFLOW_YAML)

os.makedirs("src/processes", exist_ok=True)
with open("src/processes/noop.py", "w") as f:
    f.write("""
from theus import process

@process(
    inputs=['domain_ctx'],
    outputs=['domain_ctx']
)
def noop_process(context):
    context.domain_ctx.counter += 1
    return context
""")

def get_memory_usage():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024  # MB

def run_bench():
    print("Setting up Engine...")
    g_ctx = MockGlobal()
    d_ctx = MockDomain()
    s_ctx = MockSystem(global_ctx=g_ctx, domain_ctx=d_ctx)
    
    # Enable strict mode to match production
    engine = TheusEngine(s_ctx, strict_mode=True)
    engine.scan_and_register("src/processes")
    
    # Warmup
    engine.execute_workflow("workflows/bench_leak.yaml")
    
    initial_mem = get_memory_usage()
    print(f"Initial Memory: {initial_mem:.2f} MB")
    
    iterations = 2000
    
    start_time = time.time()
    for i in range(iterations):
        engine.execute_workflow("workflows/bench_leak.yaml")
        
        if i % 100 == 0:
            mem = get_memory_usage()
            print(f"Step {i}: {mem:.2f} MB (Delta: {mem - initial_mem:.2f} MB)")
            
    end_time = time.time()
    final_mem = get_memory_usage()
    print(f"Final Memory: {final_mem:.2f} MB")
    print(f"Total Growth: {final_mem - initial_mem:.2f} MB")
    print(f"Avg Time per Step: {(end_time - start_time) / iterations * 1000:.2f} ms")

if __name__ == "__main__":
    run_bench()
