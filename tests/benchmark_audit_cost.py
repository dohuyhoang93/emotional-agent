
import time
import numpy as np

def benchmark():
    N = 100
    # Create tensors
    tensors = {
        'traces': np.random.rand(N, N).astype(np.float32),
        'weights': np.random.rand(N, N).astype(np.float32)
    }
    
    class MockCtx:
        def __init__(self):
            self.tensors = tensors
            
    ctx = MockCtx()
    
    # Operation 1: Native Numpy Mean
    start = time.time()
    for _ in range(10000):
        val = tensors['traces'].mean()
    end = time.time()
    print(f"Native Numpy Mean (10k iter): {end - start:.4f}s")
    print(f"Per Call: {(end - start)/10000 * 1e6:.4f} us")
    
    # Operation 2: Path Resolution (Simulated with proposed fix)
    def resolve_proposed(ctx, path):
        parts = path.split('.')
        current = ctx
        for p in parts:
            if isinstance(current, dict):
                current = current[p]
            elif p.endswith('()'):
                current = getattr(current, p[:-2])()
            else:
                current = getattr(current, p)
        return current
        
    start = time.time()
    for _ in range(10000):
        # Simulate resolving "tensors.traces.mean()"
        # In current audit it is broken for dicts, this tests the FIXED version cost
        val = resolve_proposed(ctx, "tensors.traces.mean()")
    end = time.time()
    print(f"Path Resolution + Mean (10k iter): {end - start:.4f}s")
    print(f"Per Call: {(end - start)/10000 * 1e6:.4f} us")

if __name__ == "__main__":
    benchmark()
