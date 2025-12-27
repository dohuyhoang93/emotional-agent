"""
SNN Core Processes for Theus Framework
=======================================
Core processes: Integrate & Fire với Theus @process decorator.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus import process
from src.core.context import SystemContext
from src.core.snn_context_theus import (
    SNNSystemContext, 
    ensure_tensors_initialized,
    sync_from_tensors,
    sync_to_tensors
)


@process(
    inputs=['domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_integrate(ctx: SystemContext):
    """
    Quy trình tích phân điện thế (Vectorized).
    Wraps _integrate_impl.
    """
    _integrate_impl(ctx, sync=True)

def _integrate_impl(ctx: SystemContext, sync: bool = True):
    """
    Internal implementation of integrate.
    Args:
        ctx: System Context
        sync: If True, sync tensors back to objects.
    """
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    # 1. Prepare Tensors
    ensure_tensors_initialized(snn_ctx)
    t = snn_ctx.domain_ctx.tensors
    
    # Unpack tensors
    pots = t['potentials']      # (N,)
    p_vecs = t['potential_vectors'] # (N, D)
    weights = t['weights']      # (N, N)
    protos = t['prototypes']    # (N, D)
    
    tau_decay = 0.9
    
    # 2. Vectorized Decay
    pots *= tau_decay
    p_vecs *= tau_decay
    
    # 3. Handle Spikes
    current_time = snn_ctx.domain_ctx.current_time
    current_spikes = snn_ctx.domain_ctx.spike_queue.get(current_time, [])
    
    if current_spikes:
        # Convert spikes to indices
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
            pots += delta_pots
            
            # 5. Integrate Vector Potential: (N, D)
            # delta_V[j] += sum_k (eff_weights[k, j] * firing_protos[k])
            # This is: eff_weights.T (N, K) @ firing_protos (K, D) -> (N, D)
            delta_vecs = np.matmul(eff_weights.T, firing_protos)
            p_vecs += delta_vecs
            
    # 6. Sync Back to Objects (Audit Compatibility)
    if sync:
        sync_from_tensors(snn_ctx)


@process(
    inputs=[
        'domain.snn_context',
        'domain.snn_context.domain_ctx.metrics'
    ],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_fire(ctx: SystemContext):
    """Quy trình bắn xung (Vectorized). Wraps _fire_impl."""
    _fire_impl(ctx, sync=True)

def _fire_impl(ctx: SystemContext, sync: bool = True):
    """Internal fire implementation."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
        
    # 1. Prepare Tensors (Assume initialized/synced by process_integrate step)
    ensure_tensors_initialized(snn_ctx) # Idempotent safety
    t = snn_ctx.domain_ctx.tensors
    
    pots = t['potentials']
    thresh = t['thresholds']
    last_fire = t['last_fire_times']
    p_vecs = t['potential_vectors']
    
    cur_time = snn_ctx.domain_ctx.current_time
    refractory = 5
    
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
            
        # Queue Logic
        if next_time not in snn_ctx.domain_ctx.spike_queue:
            snn_ctx.domain_ctx.spike_queue[next_time] = []
        snn_ctx.domain_ctx.spike_queue[next_time].extend(future_spikes)
        
    # 4. Sync Back (LastFire, Pots, PVecs changed)
    if sync:
        sync_from_tensors(snn_ctx)
    
    # Metrics
    fire_rate = len(fired_indices) / len(pots) if len(pots) > 0 else 0.0
    snn_ctx.domain_ctx.metrics['fire_rate'] = fire_rate
    snn_ctx.domain_ctx.metrics['fired_count'] = len(fired_indices)
    
@process(
    inputs=['domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_tick(ctx: SystemContext):
    """Quy trình tăng thời gian (1ms per step). Wraps _tick_impl."""
    _tick_impl(ctx)

def _tick_impl(ctx: SystemContext):
    """Internal tick implementation."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    snn_ctx.domain_ctx.current_time += 1

