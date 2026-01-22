import numpy as np
from theus.contracts import process

@process(parallel=True)
def process_partition(ctx):
    """
    Processes a specific partition of the shared data.
    """
    # 1. Get Inputs (Lightweight)
    p_id = ctx.input.get('partition_id')
    start = ctx.input.get('start_idx')
    end = ctx.input.get('end_idx')
    
    # 2. Access Shared Data (Zero-Copy)
    input_data = ctx.heavy['source_data']
    output_data = ctx.heavy['results_data']
    
    # 3. Simulate Intensive Work (CPU Bound)
    chunk = input_data[start:end]
    
    # In-Place Write (Visible to all instantly)
    processed = np.power(chunk, 2)
    output_data[start:end] = processed
    
    # 4. Return Delta (Aggregation Metadata)
    local_sum = float(np.sum(processed))
    
    return {
        "p_id": p_id,
        "partial_sum": local_sum,
        "rows_processed": (end - start),
        "pid": __import__('os').getpid()
    }

@process(parallel=True)
def saboteur_task(ctx):
    """
    Attempts to destroy the shared memory provided to it.
    This should FAIL if Theus is working correctly.
    """
    try:
        data = ctx.heavy['source_data']
        if hasattr(data, 'shm') and data.shm:
            data.shm.unlink()
            return {"status": "DESTROYED"}
        else:
            return {"status": "NO_HANDLE"}
    except PermissionError:
        return {"status": "BLOCKED"}
    except Exception as e:
        return {"status": f"ERROR: {e}"}
