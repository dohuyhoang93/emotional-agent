
import numpy as np

from theus.contracts import process

@process(parallel=True)
def process_heavy_task(ctx):
    # This runs inside a Sub-Interpreter (worker)
    # ctx.heavy is auto-wrapped by ParallelContext -> HeavyZoneWrapper
    
    # 1. Access Zero-Copy Data
    arr = ctx.heavy['matrix']
    
    # 2. Compute
    res = np.dot(arr, arr)
    
    return res.shape

def process_simple_task(ctx):
    return "Hello"
