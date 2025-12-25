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
    inputs=[
        'snn.domain.neurons',
        'snn.domain.synapses',
        'snn.domain.spike_queue',
        'snn.domain.current_time',
        'snn.global.tau_decay'
    ],
    outputs=[
        'snn.domain.neurons',
        'snn.domain.metrics'
    ],
    side_effects=[]
)
def process_integrate(ctx: SystemContext, snn_ctx: SNNSystemContext):
    """
    Quy trình tích phân điện thế với vector matching.
    
    NOTE: Theus sẽ audit:
    - tau_decay trong range [0.5, 1.0]
    - neurons không bị modify ngoài contract
    - metrics được update đúng
    """
    domain = snn_ctx.domain_ctx
    tau_decay = snn_ctx.global_ctx.tau_decay
    
    # 1. Rò rỉ điện thế (Leaky)
    for neuron in domain.neurons:
        neuron.potential *= tau_decay
        neuron.potential_vector *= tau_decay
    
    # 2. Xử lý xung đến từ spike queue
    current_spikes = domain.spike_queue.get(domain.current_time, [])
    
    if not current_spikes:
        return
    
    for spike_neuron_id in current_spikes:
        if spike_neuron_id >= len(domain.neurons):
            continue
        
        spike_neuron = domain.neurons[spike_neuron_id]
        
        for synapse in domain.synapses:
            if synapse.pre_neuron_id != spike_neuron_id:
                continue
            
            if synapse.post_neuron_id >= len(domain.neurons):
                continue
            
            post_neuron = domain.neurons[synapse.post_neuron_id]
            
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
        'snn.domain.neurons',
        'snn.domain.current_time',
        'snn.global.refractory_period'
    ],
    outputs=[
        'snn.domain.neurons',
        'snn.domain.spike_queue',
        'snn.domain.metrics'
    ],
    side_effects=[]
)
def process_fire(ctx: SystemContext, snn_ctx: SNNSystemContext):
    """Quy trình bắn xung khi potential vượt threshold."""
    domain = snn_ctx.domain_ctx
    refractory_period = snn_ctx.global_ctx.refractory_period
    
    fired_neurons = []
    
    for neuron in domain.neurons:
        time_since_last_fire = domain.current_time - neuron.last_fire_time
        if time_since_last_fire < refractory_period:
            continue
        
        if neuron.potential >= neuron.threshold:
            fired_neurons.append(neuron.neuron_id)
            neuron.last_fire_time = domain.current_time
            neuron.fire_count += 1
            neuron.potential = -0.1
            neuron.potential_vector = np.zeros(neuron.vector_dim)
    
    if fired_neurons:
        next_time = domain.current_time + 1
        if next_time not in domain.spike_queue:
            domain.spike_queue[next_time] = []
        domain.spike_queue[next_time].extend(fired_neurons)
    
    fire_rate = len(fired_neurons) / len(domain.neurons) if domain.neurons else 0.0
    domain.metrics['fire_rate'] = fire_rate
    domain.metrics['fired_count'] = len(fired_neurons)


@process(
    inputs=['snn.domain.current_time'],
    outputs=['snn.domain.current_time'],
    side_effects=[]
)
def process_tick(ctx: SystemContext, snn_ctx: SNNSystemContext):
    """Quy trình tăng thời gian (1ms per step)."""
    snn_ctx.domain_ctx.current_time += 1
