
import numpy as np
import time
from theus.contracts import process

@process(parallel=True)
def apply_filter(ctx):
    """
    Applies a simple filter to a large matrix (Zero-Copy).
    Expected context:
      - ctx.heavy['image']: Read-Only ShmArray (Result of Zero-Copy)
      - ctx.input['kernel_size']: int
    """
    # 1. Access Zero-Copy Data (No Deserialization Cost)
    # Theus automatically maps the shared buffer to a numpy array here.
    image = ctx.heavy['image'] 
    k = ctx.input.get('kernel_size', 1)
    
    # 2. Simulate Work
    # Simple operation: element-wise multiplication or similar
    # In real world: convolution, detection, etc.
    result_slice = image[0:100, 0:100] * k 
    
    # 3. Return Metadata/Result
    # (We don't return the big array to avoid Pickle cost on return path)
    return {
        "status": "processed",
        "sample_mean": float(np.mean(result_slice)),
        "shape": image.shape,
        "pid": __import__('os').getpid()
    }
