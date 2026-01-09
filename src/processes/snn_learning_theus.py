"""
SNN Learning Processes for Theus Framework
===========================================
Learning processes: Clustering & STDP với Theus @process decorator.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from theus.contracts import process


@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=['domain_ctx', 'domain_ctx.snn_context'],
    side_effects=[]
)
def process_clustering(ctx):
    """
    Quy trình học không gian (Unsupervised Clustering). Wraps _clustering_impl.
    """
    _clustering_impl(ctx)

def _clustering_impl(ctx):
    """
    Internal Clustering implementation (Vectorized Wrapper).
    """
    _clustering_impl_vectorized(ctx)

def _clustering_impl_vectorized(ctx):
    """
    Vectorized Clustering implementation.
    
    Logic:
    1. Identify firing neurons (spikes)
    2. Get their prototype vectors
    3. For each spike, identify connected post-neurons
    4. Move post-neurons' prototypes closer to spike's prototype (Hebbian)
    5. Normalize
    """
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    
    # Ensure Infrastructure
    from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
    ensure_heavy_tensors_initialized(snn_ctx)
    
    t = domain.heavy_tensors
    weights = t['weights']          # (N, N)
    protos = t['prototypes']        # (N, D)
    
    learning_rate = 0.001
    cur_time = domain.current_time
    
    current_spikes = domain.spike_queue.get(cur_time, [])
    if not current_spikes:
        return # No sync needed if no change
        
    spike_indices = np.array(current_spikes, dtype=int)
    N = len(weights)
    spike_indices = spike_indices[(spike_indices >= 0) & (spike_indices < N)]
    
    if len(spike_indices) == 0:
        return
        
    # Hebbian Learning: For each spike, update connected post-neurons
    # Since spikes are few (sparsity), iterating spikes is acceptable.
    # But updating post-neurons should be vectorized.
    
    firing_protos = protos[spike_indices] # (K, D)
    
    for k, spike_id in enumerate(spike_indices):
        # Identify connected post-neurons
        # weights[spike_id, :] > 0 is mask (N,)
        connected_posts_mask = weights[spike_id, :] > 0
        
        if not connected_posts_mask.any():
            continue
            
        # Get indices of connected post-neurons
        post_indices = np.where(connected_posts_mask)[0]
        
        # Vectorized Update
        # direction = spike_proto - protos[post_indices]
        # protos[post_indices] += lr * direction
        
        spike_proto = firing_protos[k] # (D,)
        
        # Broadcasting: (D,) - (M, D) -> (M, D)
        delta = spike_proto - protos[post_indices]
        protos[post_indices] += learning_rate * delta
        
        # Normalize updated prototypes
        # (M, D)
        norms = np.linalg.norm(protos[post_indices], axis=1, keepdims=True) # (M, 1)
        norms = np.maximum(norms, 1e-8)
        protos[post_indices] /= norms
    
    # Sync Back
    sync_from_heavy_tensors(snn_ctx)


@process(
    inputs=['domain_ctx', 'domain_ctx.snn_context'],
    outputs=['domain_ctx', 'domain_ctx.snn_context'],
    side_effects=[]
)
def process_stdp(ctx):
    """
    Quy trình STDP (Spike-Timing-Dependent Plasticity). Wraps _stdp_impl.
    """
    _stdp_impl(ctx)

def _stdp_impl(ctx):
    """
    Internal STDP implementation (Vectorized Wrapper).
    Logic gốc đã được thay thế bằng _stdp_impl_vectorized.
    """
    _stdp_impl_vectorized(ctx)

def _stdp_impl_vectorized(ctx):
    """
    Vectorized STDP implementation.
    
    Logic:
    1. Update weights & traces decay (Vectorized)
    2. Update traces based on pre-spikes (Masked Vectorized)
    3. LTP: Pre-spikes -> Update weights based on traces (Masked Broadcast)
    4. LTD: Post-spikes -> Update weights based on traces (Masked Broadcast)
    """
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    
    # 0. Ensure Infrastructure
    from src.core.snn_context_theus import ensure_heavy_tensors_initialized, sync_from_heavy_tensors
    ensure_heavy_tensors_initialized(snn_ctx)
    
    t = domain.heavy_tensors
    weights = t['weights']          # (N, N)
    traces = t['traces']            # (N, N)
    last_fire = t['last_fire_times'] # (N,)
    
    # Parameters
    learning_rate = 0.01  # Should come from global_ctx but hardcoded in original
    tau_trace = 0.9
    weight_decay = 0.9999
    time_window = 20
    cur_time = domain.current_time
    
    # 1. Decay Laws (Vectorized)
    weights *= weight_decay
    traces *= tau_trace
    
    # 2. Check Spikes
    current_spikes = domain.spike_queue.get(cur_time, [])
    if not current_spikes:
        sync_from_heavy_tensors(snn_ctx)
        return

    # Filter valid spikes
    N = len(weights)
    spike_indices = np.array(current_spikes, dtype=int)
    spike_indices = spike_indices[(spike_indices >= 0) & (spike_indices < N)]
    
    if len(spike_indices) == 0:
        sync_from_tensors(snn_ctx)
        return
        
    # 3. Update Traces (Pre-synaptic spikes increase trace)
    # traces[i, :] += 1.0 for all i in spike_indices
    # But only for EXISTING synapses (weights > 0)
    # Mask: (K, N)
    mask_connectivity = weights[spike_indices, :] > 0
    traces[spike_indices, :] += mask_connectivity.astype(np.float32)
    
    # 4. LTP: Pre-neuron fired (spike_indices), check Post-neurons
    # Logic: If Pre fired NOW, and Post fired RECENTLY (0 < dt < window) -> Weighted += Trace
    
    # Time diffs: cur_time - last_fire[j] for all j
    # (N,) array
    time_diffs_post = cur_time - last_fire
    
    # Broadcast to (K, N) where K is num spikes
    # We want to check for each spike i, and each post j
    # This is efficiently just reusing time_diffs_post rows? No.
    # time_diffs_post is 1D (N,). condition is element-wise on j.
    # So we can create a mask for eligible post-neurons FIRST.
    
    # Eligible Post Neurons: fired within (0, window)
    # Note: last_fire is updated in FIRE process BEFORE this?
    # Usually Integrate -> Fire -> STDP.
    # If Post fired THIS step, last_fire == cur_time -> diff = 0.
    # Original logic: 0 < time_diff < window. So diff=0 is excluded?
    # Original: time_diff = cur_time - post_neuron.last_fire_time
    # If post fired now, last_fire is cur_time. diff=0.
    # So LTP excludes simultaneous firing?
    # Checking original: "if 0 < time_diff < time_window". Yes.
    
    ltp_post_mask = (time_diffs_post > 0) & (time_diffs_post < time_window) # (N,)
    
    # Apply to all rows corresponding to spike_indices
    # But we also need connectivity mask
    # Mask of (i, j) where i in spikes, j in ltp_eligible, and weight > 0
    
    # (K, N)
    ltp_update_mask = mask_connectivity & ltp_post_mask[np.newaxis, :]
    
    # Update weights
    # weights[i, j] += lr * traces[i, j]
    delta_ltp = learning_rate * traces[spike_indices, :]
    weights[spike_indices, :] += delta_ltp * ltp_update_mask.astype(np.float32)
    
    # 5. LTD: Post-neuron fired (spike_indices), check Pre-neurons
    # Logic: If Post fired NOW, and Pre fired RECENTLY -> Weight -= decay
    
    # Here spike_indices represent POST neurons
    # Check PRE neurons (j) for each spike (i)
    # diff = cur_time - last_fire[j]
    
    time_diffs_pre = cur_time - last_fire # (N,)
    ltd_pre_mask = (time_diffs_pre > 0) & (time_diffs_pre < time_window) # (N,)
    
    # Connectivity: weights[j, i] > 0 where i is spike (post)
    # Transpose view: weights[:, spike_indices] is (N, K)
    w_pre_post = weights[:, spike_indices]
    mask_connectivity_bg = w_pre_post > 0
    
    # Mask (N, K)
    ltd_update_mask = mask_connectivity_bg & ltd_pre_mask[:, np.newaxis]
    
    # Update weights
    # weights[j, i] -= lr * 0.5
    delta_ltd = learning_rate * 0.5
    weights[:, spike_indices] -= delta_ltd * ltd_update_mask.astype(np.float32)
    
    # 6. Clip Weights
    # Only need to clip modified rows/cols? Efficient enough to clip all or just subset.
    # Clipping subset is complex. Clipping all is O(N^2).
    # Optimize: Clip only modified.
    
    # LTP affected: weights[spike_indices, :]
    weights[spike_indices, :] = np.clip(weights[spike_indices, :], 0.0, 1.0)
    
    # LTD affected: weights[:, spike_indices]
    weights[:, spike_indices] = np.clip(weights[:, spike_indices], 0.0, 1.0)
    
    # 7. Sync Back
    sync_from_tensors(snn_ctx)

