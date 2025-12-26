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
from src.core.snn_context_theus import SNNSystemContext


@process(
    inputs=['domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_integrate(ctx: SystemContext):
    """
    Quy trình tích phân điện thế với vector matching.
    
    NOTE: Theus sẽ audit:
    - tau_decay trong range [0.5, 1.0]
    - neurons không bị modify ngoài contract
    - metrics được update đúng
    """
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    tau_decay = 0.9  # Default tau_decay
    
    # 1. Rò rỉ điện thế (Leaky)
    for neuron in snn_ctx.domain_ctx.neurons:
        neuron.potential *= tau_decay
        neuron.potential_vector *= tau_decay
    
    # 2. Xử lý xung đến từ spike queue
    current_spikes = snn_ctx.domain_ctx.spike_queue.get(snn_ctx.domain_ctx.current_time, [])
    
    if not current_spikes:
        return
    
    for spike_neuron_id in current_spikes:
        if spike_neuron_id >= len(snn_ctx.domain_ctx.neurons):
            continue
        
        spike_neuron = snn_ctx.domain_ctx.neurons[spike_neuron_id]
        
        for synapse in snn_ctx.domain_ctx.synapses:
            if synapse.pre_neuron_id != spike_neuron_id:
                continue
            
            if synapse.post_neuron_id >= len(snn_ctx.domain_ctx.neurons):
                continue
            
            post_neuron = snn_ctx.domain_ctx.neurons[synapse.post_neuron_id]
            
            # Vector matching
            norm_spike = np.linalg.norm(spike_neuron.prototype_vector)
            norm_post = np.linalg.norm(post_neuron.prototype_vector)
            
            if norm_spike == 0 or norm_post == 0:
                similarity = 0.0
            else:
                similarity = np.dot(
                    spike_neuron.prototype_vector,
                    post_neuron.prototype_vector
                ) / (norm_spike * norm_post)
            
            effective_weight = synapse.weight * max(0, similarity)
            post_neuron.potential += effective_weight
            post_neuron.potential_vector += (
                effective_weight * spike_neuron.prototype_vector
            )


@process(
    inputs=[
        'domain.snn_context',
        'domain.snn_context.domain_ctx.metrics' # Added
    ],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_fire(ctx: SystemContext):
    """Quy trình bắn xung khi potential vượt threshold."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    refractory_period = 5  # Default refractory period
    
    fired_neurons = []
    
    for neuron in snn_ctx.domain_ctx.neurons:
        time_since_last_fire = snn_ctx.domain_ctx.current_time - neuron.last_fire_time
        if time_since_last_fire < refractory_period:
            continue
        
        if neuron.potential >= neuron.threshold:
            fired_neurons.append(neuron.neuron_id)
            neuron.last_fire_time = snn_ctx.domain_ctx.current_time
            neuron.fire_count += 1
            neuron.potential = -0.1
            neuron.potential_vector = np.zeros(neuron.vector_dim)
    
    if fired_neurons:
        next_time = snn_ctx.domain_ctx.current_time + 1
        if next_time not in snn_ctx.domain_ctx.spike_queue:
            snn_ctx.domain_ctx.spike_queue[next_time] = []
        snn_ctx.domain_ctx.spike_queue[next_time].extend(fired_neurons)
    
    fire_rate = len(fired_neurons) / len(snn_ctx.domain_ctx.neurons) if snn_ctx.domain_ctx.neurons else 0.0
    snn_ctx.domain_ctx.metrics['fire_rate'] = fire_rate
    snn_ctx.domain_ctx.metrics['fired_count'] = len(fired_neurons)


@process(
    inputs=['domain.snn_context'],
    outputs=['domain.snn_context'],
    side_effects=[]
)
def process_tick(ctx: SystemContext):
    """Quy trình tăng thời gian (1ms per step)."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    if snn_ctx is None:
        return
    
    snn_ctx.domain_ctx.current_time += 1

