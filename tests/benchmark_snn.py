
import sys
import time
sys.path.append('.')

from src.core.context import GlobalContext
from src.core.snn_context_theus import create_snn_context_theus
from src.processes.snn_core_theus import process_integrate, process_fire, process_tick

def benchmark_snn():
    print("="*60)
    print("SNN BENCHMARK (Theus Process-Oriented)")
    print("="*60)
    
    # 1. Setup
    num_neurons = 500
    steps = 1000
    
    print(f"Configuration: Neurons={num_neurons}, Steps={steps}")
    
    snn_system_ctx = create_snn_context_theus(num_neurons=num_neurons, connectivity=0.2)
    
    # Wrap in SystemContext used by Theus
    # We need a dummy global context
    global_ctx = GlobalContext()
    
    # The processes expect `ctx.domain_ctx.snn_context`
    # We need to construct a SystemContext that has `domain_ctx.snn_context`
    # Let's mock the structure needed by snn_core_theus.py
    # snn_ctx = ctx.domain_ctx.snn_context
    
    class MockDomain:
        def __init__(self, snn_ctx):
            self.snn_context = snn_ctx
            self.current_time = 0
            self.metrics = {}
    
    class MockSystemContext:
        def __init__(self, snn_context):
            self.domain_ctx = MockDomain(snn_context)
            self.global_ctx = global_ctx

    system_ctx = MockSystemContext(snn_system_ctx)
    
    # Pre-warm
    print("Pre-warming JIT/Caches...")
    for _ in range(10):
        process_integrate(system_ctx)
        process_fire(system_ctx)
        process_tick(system_ctx)
        
    # Benchmark
    print("Running Benchmark...")
    start_time = time.time()
    
    for i in range(steps):
        process_integrate(system_ctx)
        process_fire(system_ctx)
        process_tick(system_ctx)
        
        if (i+1) % 100 == 0:
            print(f"Step {i+1}/{steps}...", end='\r')
            
    end_time = time.time()
    duration = end_time - start_time
    sps = steps / duration
    
    print(f"\nCompleted in {duration:.4f}s")
    print(f"Speed: {sps:.2f} Steps/Second")
    print(f"Metrics: {system_ctx.domain_ctx.snn_context.domain_ctx.metrics}")
    print("="*60)

if __name__ == "__main__":
    benchmark_snn()
