"""
Tensor Leak Analysis Script
Identifies which PyTorch tensors are accumulating in memory.
"""
import gc
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, 'src')
sys.path.insert(0, '.')

import torch
from collections import Counter, defaultdict

def analyze_tensors():
    """Analyze all PyTorch tensors in memory."""
    gc.collect()
    
    tensors = []
    for obj in gc.get_objects():
        try:
            if torch.is_tensor(obj):
                tensors.append(obj)
        except:
            pass
    
    print(f"\n{'='*60}")
    print(f"TOTAL TENSORS: {len(tensors)}")
    print(f"{'='*60}")
    
    # Group by shape
    shape_counter = Counter()
    shape_memory = defaultdict(int)
    
    for t in tensors:
        shape = str(tuple(t.shape))
        shape_counter[shape] += 1
        shape_memory[shape] += t.element_size() * t.nelement()
    
    print("\nTop 20 shapes by COUNT:")
    for shape, count in shape_counter.most_common(20):
        mem_kb = shape_memory[shape] / 1024
        print(f"  {shape:30s} x {count:5d}  ({mem_kb:.1f} KB total)")
    
    # Group by dtype
    print("\nBy dtype:")
    dtype_counter = Counter(str(t.dtype) for t in tensors)
    for dtype, count in dtype_counter.most_common():
        print(f"  {dtype}: {count}")
    
    # Tensors attached to computation graph (requires_grad or grad_fn)
    grad_tensors = [t for t in tensors if t.requires_grad or t.grad_fn is not None]
    print(f"\nTensors with gradients/graph: {len(grad_tensors)} / {len(tensors)}")
    
    if grad_tensors:
        print("\nTop gradient tensor shapes:")
        grad_shape_counter = Counter(str(tuple(t.shape)) for t in grad_tensors)
        for shape, count in grad_shape_counter.most_common(10):
            print(f"  {shape}: {count}")
    
    return tensors

def find_tensor_referrers(tensors, max_samples=5):
    """Find what's holding references to tensors."""
    print(f"\n{'='*60}")
    print("TENSOR REFERRER ANALYSIS")
    print(f"{'='*60}")
    
    # Sample some tensors of common shapes
    shape_counter = Counter(str(tuple(t.shape)) for t in tensors)
    common_shapes = [s for s, _ in shape_counter.most_common(5)]
    
    for target_shape in common_shapes:
        print(f"\nAnalyzing shape {target_shape}:")
        samples = [t for t in tensors if str(tuple(t.shape)) == target_shape][:max_samples]
        
        for i, t in enumerate(samples):
            refs = gc.get_referrers(t)
            ref_types = Counter(type(r).__name__ for r in refs)
            print(f"  Sample {i}: refs={len(refs)}, types={dict(ref_types.most_common(3))}")

if __name__ == "__main__":
    print("Loading modules...")
    
    # Import to load torch models
    from core.context import SystemContext, GlobalContext, DomainContext
    from core.snn_context_theus import SNNSystemContext, SNNGlobalContext, SNNDomainContext
    
    print("Initial tensor analysis (after imports only):")
    initial_tensors = analyze_tensors()
    
    print("\n" + "="*60)
    print("To see accumulation, run a few steps and analyze again.")
    print("="*60)
