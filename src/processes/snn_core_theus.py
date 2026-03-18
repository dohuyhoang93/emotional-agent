"""
SNN Core Processes for Theus Framework
=======================================
Core processes: Integrate & Fire với Theus @process decorator.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus.contracts import process
from src.core.context import SystemContext
from src.core.snn_context_theus import (
    ensure_heavy_tensors_initialized,
    sync_from_heavy_tensors
)
from src.logger import log


@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=[],
    side_effects=[]
)
def process_integrate(ctx: SystemContext):
    """
    Step 1: Integration (Decay + Sum Inputs).
    """
    try:
        delta = _integrate_impl(ctx)
        return delta
    except Exception:
        import traceback
        ctx.log(f"CRASH in process_integrate: {traceback.format_exc()}", level="error")
        raise
    return {}


def _integrate_impl(ctx: SystemContext, sync: bool = True):
    """
    Internal implementation of integrate.
    Args:
        ctx: System Context
        sync: If True, sync tensors back to objects.
    """
    # Resolve SNN Context (Handle nested RL Context vs Standalone SNN Context)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    if snn_ctx is None:
        return
    
    # 1. Prepare Tensors
    ensure_heavy_tensors_initialized(snn_ctx)
    t = snn_ctx.domain_ctx.heavy_tensors
    
    # Unpack tensors
    pots = t['potentials']      # (N,)
    p_vecs = t['potential_vectors'] # (N, D)
    weights = t['weights']      # (N, N)
    protos = t['prototypes']    # (N, D)
    
    try:
        tau_decay = float(snn_ctx.global_ctx.tau_decay)
    except (TypeError, AttributeError):
        tau_decay = 0.9
    
    # 2. Vectorized Decay
    # print(f"DEBUG INTEGRATE: BEFORE Decay, pots[:3]={pots[:3]}")
    pots *= tau_decay
    p_vecs *= tau_decay
    # print(f"DEBUG INTEGRATE: AFTER Decay, pots[:3]={pots[:3]}")
    
    # 3. Handle Spikes (Vectorized Buffer)
    try:
        current_time = int(snn_ctx.domain_ctx.current_time)
    except (TypeError, AttributeError):
        current_time = 0
    
    use_vectorized = t.get('use_vectorized_queue', False)
    
    if use_vectorized:
        # Read from Spike Buffer
        spike_buffer = t['spike_buffer']
        buffer_size = spike_buffer.shape[0]
        t_idx = current_time % buffer_size
        
        # Get firing neurons (indices where buffer == 1)
        current_spikes_mask = spike_buffer[t_idx] > 0
        spike_indices = np.where(current_spikes_mask)[0]
        
        # Clear buffer slot for reuse (circular)
        spike_buffer[t_idx] = 0
    else:
        # Legacy Dict Loop
        current_spikes = snn_ctx.domain_ctx.spike_queue.get(current_time, [])
        spike_indices = np.array(current_spikes, dtype=int)
        
    # Filter out invalid indices
    N = len(pots)
    spike_indices = spike_indices[spike_indices < N]
        
    if len(spike_indices) > 0:
        # Gather Firing Prototypes: (K, D)
        firing_protos = protos[spike_indices]
        
        # Compute Similarity Matrix: (K, N)
        # Sim[k, j] = dot(Proto_k, Proto_j)
        # Assumes protos are normalized!
        sim_matrix = np.matmul(firing_protos, protos.T)
        
        # ReLU (Similarity > 0)
        sim_matrix = np.maximum(0, sim_matrix)
        
        # Gather Weights: (K, N) - Row k corresponds to weights FROM spike_k TO all j
        # Connectivity matrix W[i, j] is weight i->j
        firing_weights = weights[spike_indices, :]
        
        # Effective Weights: (K, N)
        eff_weights = firing_weights * sim_matrix
        
        # 4. Integrate Scalar Potential: (N,)
        # Sum contributions from all K spikes for each neuron j
        delta_pots = np.sum(eff_weights, axis=0) # Sum over K (rows) -> (N,)
        
        # GLOBAL INHIBITION (Prevent Seizures)
        # Normalize synaptic input by the level of network activity
        activity_level = len(spike_indices) / max(1, N)
        
        # We expect a baseline sparse activity (e.g., 2% of network = ~20 neurons for N=1024)
        # We only start throttling heavily if spikes exceed expected sparse baseline.
        expected_spikes = max(10, int(N * 0.02))
        
        if len(spike_indices) > expected_spikes:
            norm_factor = 1.0 + ((len(spike_indices) - expected_spikes) / (expected_spikes * 2.0))
        else:
            norm_factor = 1.0
            
        delta_pots /= norm_factor
        
        pots += delta_pots
        
        # 5. Integrate Vector Potential: (N, D)
        # delta_V[j] += sum_k (eff_weights[k, j] * firing_protos[k])
        # This is: eff_weights.T (N, K) @ firing_protos (K, D) -> (N, D)
        delta_vecs = np.matmul(eff_weights.T, firing_protos)
        p_vecs += delta_vecs
        
    # 6. Sync Back to Objects (Audit Compatibility)
    if sync:
        sync_from_heavy_tensors(snn_ctx)

    return {'heavy_tensors': t}


@process(
    inputs=['domain_ctx', 
        'domain_ctx.snn_context',
        'domain_ctx.snn_context.domain_ctx.metrics'
    ],
    outputs=['domain_ctx.snn_context.domain_ctx.metrics', 'domain_ctx.snn_context.domain_ctx.heavy_tensors'],
    side_effects=[]
)
def process_fire(ctx: SystemContext):  # noqa: F811
    """Quy trình bắn xung (Vectorized). Wraps _fire_impl."""
    try:
        delta = _fire_impl(ctx, sync=True)
        return delta
    except Exception:
        import traceback
        ctx.log(f"CRASH in process_fire: {traceback.format_exc()}", level="error")
        raise
    return {}

def _fire_impl(ctx: SystemContext, sync: bool = True):
    """Internal fire implementation."""
    # Resolve SNN Context (Handle nested RL Context vs Standalone SNN Context)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    if snn_ctx is None:
        return
        
    # 1. Prepare Tensors (Assume initialized/synced by process_integrate step)
    ensure_heavy_tensors_initialized(snn_ctx) # Idempotent safety
    t = snn_ctx.domain_ctx.heavy_tensors
    
    pots = t['potentials']
    thresh = t['thresholds']
    last_fire = t['last_fire_times']
    p_vecs = t['potential_vectors']
    
    try:
        cur_time = int(snn_ctx.domain_ctx.current_time)
    except (TypeError, AttributeError):
        cur_time = 0
    refractory = 5
    
    # DEBUG: Tensor State - DISABLED for Production
    # if cur_time % 100 == 0:
    #      print(f"DEBUG CORE: Time={cur_time}, Max Pot: {np.max(pots):.4f}, Min Thresh: {np.min(thresh):.4f}, Spikes: {len(np.where((pots >= thresh) & ((cur_time - last_fire) >= refractory))[0])}")
    
    # 2. Vectorized Condition Check
    # (P >= Thresh) & (Time - Last >= Refractory)
    can_fire = (pots >= thresh) & ((cur_time - last_fire) >= refractory)
    
    # Get indices
    fired_indices = np.where(can_fire)[0]
    
    # 3. Updates
    if len(fired_indices) > 0:
        # Update Tensors
        last_fire[fired_indices] = cur_time
        pots[fired_indices] = -0.1
        p_vecs[fired_indices] = 0.0 # Clear vector
        
        # Update Objects and Queue (Hybrid part)
        # We need to update fire_count manually on objects as we don't tensorize it
        # Also need to add to spike_queue
        
        neurons = snn_ctx.domain_ctx.neurons
        next_time = cur_time + 1
        future_spikes = []
        
        for idx in fired_indices:
            idx = int(idx) # convert numpy int to python int
            future_spikes.append(idx)
            
            # Non-tensor Metrics
            neurons[idx].fire_count += 1
            
        # Queue Logic (Hybrid: Object + Vectorized)
        
        use_vectorized = t.get('use_vectorized_queue', False)
        delay = 1 # Standard Delay check logic later
        
        if use_vectorized:
            # Write to Spike Buffer
            spike_buffer = t['spike_buffer']
            buffer_size = spike_buffer.shape[0]
            t_idx = (cur_time + delay) % buffer_size
            
            # Set fired indices to 1 (or accumulate if counting)
            spike_buffer[t_idx, fired_indices] = 1
        else:
            # Legacy Dict
            if next_time not in snn_ctx.domain_ctx.spike_queue:
                snn_ctx.domain_ctx.spike_queue[next_time] = []
            snn_ctx.domain_ctx.spike_queue[next_time].extend(future_spikes)
        
    # Metrics
    fire_rate = len(fired_indices) / len(pots) if len(pots) > 0 else 0.0
    
    # DEBUG: Log firing activity occasionally
    if len(fired_indices) > 0:
        log(snn_ctx, "debug", f"DEBUG SNN FIRE: Time={cur_time}, Fired={len(fired_indices)}, Rate={fire_rate:.4f}")

    metrics = snn_ctx.domain_ctx.metrics
    metrics['fire_rate'] = fire_rate
    metrics['fired_count'] = len(fired_indices)
    
    # Cumulative Update (Running Average) -> Thay bằng Exponential Moving Average (EMA)
    # Điều này loại bỏ hoàn toàn sự phụ thuộc vào số ticks tích lũy từ đầu, 
    # giúp Rate phản ánh chính xác hoạt động của Episode hiện tại.
    alpha_ema = 0.05 # Tốc độ cập nhật trung bình (5% step mới, 95% lịch sử gần)
    current_avg = metrics.get('avg_firing_rate', 0.0)
    metrics['avg_firing_rate'] = (1.0 - alpha_ema) * current_avg + alpha_ema * fire_rate

    # Final Delta construction
    delta = {
        'heavy_tensors': t,
        'metrics': metrics
    }
    
    return delta
    
@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=['domain_ctx.snn_context.domain_ctx.current_time'],
    side_effects=[]
)
def process_tick(ctx: SystemContext):
    """Quy trình tăng thời gian (1ms per step). Wraps _tick_impl."""
    return _tick_impl(ctx)

def _tick_impl(ctx: SystemContext):
    """Internal tick implementation."""
    # Resolve SNN Context (Handle nested RL Context vs Standalone SNN Context)
    snn_ctx = ctx
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'snn_context') and ctx.domain_ctx.snn_context is not None:
        snn_ctx = ctx.domain_ctx.snn_context
    if snn_ctx is None:
        return {}
    
    # Safe increment
    now = int(snn_ctx.domain_ctx.current_time)
    
    # === MEMORY LEAK FIX: Cleanup old spike_queue entries ===
    spike_queue = snn_ctx.domain_ctx.spike_queue
    buffer_window = 10  # Keep last 10 time steps for safety
    
    # Remove old entries
    old_times = [t for t in spike_queue.keys() if t < now - buffer_window]
    for t in old_times:
        del spike_queue[t]
        
    return {'current_time': now + 1}

