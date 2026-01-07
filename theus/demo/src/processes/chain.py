import time
from theus import process
from src.context import DemoSystemContext

# Decorator enforces Contract (Input/Output Safety)

@process(
    inputs=[], 
    outputs=['domain.status'],
    side_effects=['I/O']
)
def p_init(ctx: DemoSystemContext):
    print("   [p_init] Initializing System Resources...")
    ctx.domain_ctx.status = "READY"
    time.sleep(0.5) # Simulate IO
    return "Initialized"

@process(
    inputs=['domain.status', 'domain.items', 'domain.processed_count'],
    outputs=['domain.status', 'domain.processed_count', 'domain.items'],
    side_effects=['I/O']
)
def p_process(ctx: DemoSystemContext):
    print(f"   [p_process] Processing Batch (Current: {ctx.domain_ctx.processed_count})...")
    
    # Simulate Work
    ctx.domain_ctx.status = "PROCESSING"
    time.sleep(1.0) # Simulate Heavy Compute
    
    # Logic
    ctx.domain_ctx.processed_count += 10
    ctx.domain_ctx.items.append(f"Batch_{ctx.domain_ctx.processed_count}")
    
    return "Processed"

@process(
    inputs=['domain.status'], 
    outputs=['domain.status'],
    side_effects=['I/O']
)
def p_finalize(ctx: DemoSystemContext):
    print("   [p_finalize] Finalizing and Cleaning up...")
    ctx.domain_ctx.status = "SUCCESS"
    time.sleep(0.5)
    print("\n   ✨ [WORKFLOW COMPLETE] Press ENTER to continue...", end="", flush=True) 
    return "Done"
