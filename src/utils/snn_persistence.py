"""
SNN Save/Load Utilities
========================
Utilities để lưu và load trained SNN agents.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import json
import os
import numpy as np
from typing import Dict, Any, List
from src.core.snn_context_theus import SNNSystemContext


def save_snn_agent(
    snn_ctx: SNNSystemContext,
    rl_ctx: Any, # SystemContext (optional)
    agent_id: int,
    output_dir: str
) -> str:
    """
    Lưu SNN agent vào file JSON.
    
    Args:
        snn_ctx: SNN system context
        agent_id: Agent ID
        output_dir: Output directory
        
    Returns:
        filepath: Path to saved file
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract state
    state = {
        'agent_id': agent_id,
        'metadata': {
            'num_neurons': len(snn_ctx.domain_ctx.neurons),
            'num_synapses': len(snn_ctx.domain_ctx.synapses),
            'vector_dim': snn_ctx.global_ctx.vector_dim,
        },
        'neurons': [],
        'synapses': [],
        'memory': {
            'q_table': {},
            'beliefs': {},
            'short_term': []
        }
    }
    
    # Save RL Memory
    if rl_ctx:
        domain = rl_ctx.domain_ctx
        state['memory']['q_table'] = domain.q_table
        state['memory']['beliefs'] = domain.believed_switch_states
        # Save short term (simplified)
        state['memory']['short_term'] = [str(x) for x in domain.short_term_memory][-10:] # Last 10

    
    # Save neurons
    for neuron in snn_ctx.domain_ctx.neurons:
        neuron_data = {
            'neuron_id': neuron.neuron_id,
            'prototype_vector': neuron.prototype_vector.tolist(),
            'threshold': float(neuron.threshold),
            'fire_count': int(neuron.fire_count),
        }
        state['neurons'].append(neuron_data)
    
    # Save synapses
    for synapse in snn_ctx.domain_ctx.synapses:
        synapse_data = {
            'synapse_id': synapse.synapse_id,
            'pre_neuron_id': synapse.pre_neuron_id,
            'post_neuron_id': synapse.post_neuron_id,
            'weight': float(synapse.weight),
            'commit_state': int(synapse.commit_state),
            'consecutive_correct': int(synapse.consecutive_correct),
            'consecutive_wrong': int(synapse.consecutive_wrong),
            'fitness': float(synapse.fitness),
        }
        state['synapses'].append(synapse_data)
    
    # Save to file
    filepath = os.path.join(output_dir, f'agent_{agent_id}_snn.json')
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2)
    
    return filepath


def load_snn_agent(
    snn_ctx: SNNSystemContext,
    filepath: str
) -> bool:
    """
    Load SNN agent từ file JSON.
    
    Args:
        snn_ctx: SNN system context (sẽ được update)
        filepath: Path to saved file
        
    Returns:
        success: True if loaded successfully
    """
    if not os.path.exists(filepath):
        return False
    
    # Load state
    with open(filepath, 'r') as f:
        state = json.load(f)
    
    # Verify metadata
    if len(snn_ctx.domain_ctx.neurons) != state['metadata']['num_neurons']:
        print(f"Warning: Neuron count mismatch: {len(snn_ctx.domain_ctx.neurons)} vs {state['metadata']['num_neurons']}")
        return False
    
    if len(snn_ctx.domain_ctx.synapses) != state['metadata']['num_synapses']:
        print(f"Warning: Synapse count mismatch: {len(snn_ctx.domain_ctx.synapses)} vs {state['metadata']['num_synapses']}")
        return False
    
    # Restore neurons
    for i, neuron_data in enumerate(state['neurons']):
        if i < len(snn_ctx.domain_ctx.neurons):
            neuron = snn_ctx.domain_ctx.neurons[i]
            neuron.prototype_vector = np.array(neuron_data['prototype_vector'], dtype=np.float32)
            neuron.threshold = neuron_data['threshold']
            neuron.fire_count = neuron_data['fire_count']
    
    # Restore synapses
    for i, synapse_data in enumerate(state['synapses']):
        if i < len(snn_ctx.domain_ctx.synapses):
            synapse = snn_ctx.domain_ctx.synapses[i]
            synapse.weight = synapse_data['weight']
            synapse.commit_state = synapse_data['commit_state']
            synapse.consecutive_correct = synapse_data['consecutive_correct']
            synapse.consecutive_wrong = synapse_data['consecutive_wrong']
            synapse.fitness = synapse_data['fitness']
    
    return True


def save_all_agents(
    agents_snn_contexts: List[SNNSystemContext],
    output_dir: str
) -> List[str]:
    """
    Lưu tất cả agents.
    
    Args:
        agents_snn_contexts: List of SNN contexts
        output_dir: Output directory
        
    Returns:
        filepaths: List of saved filepaths
    """
    filepaths = []
    
    for agent_id, snn_ctx in enumerate(agents_snn_contexts):
        filepath = save_snn_agent(snn_ctx, agent_id, output_dir)
        filepaths.append(filepath)
        print(f"Saved agent {agent_id} to {filepath}")
    
    return filepaths


def load_all_agents(
    agents_snn_contexts: List[SNNSystemContext],
    input_dir: str
) -> int:
    """
    Load tất cả agents.
    
    Args:
        agents_snn_contexts: List of SNN contexts (sẽ được update)
        input_dir: Input directory
        
    Returns:
        count: Number of agents loaded successfully
    """
    count = 0
    
    for agent_id, snn_ctx in enumerate(agents_snn_contexts):
        filepath = os.path.join(input_dir, f'agent_{agent_id}_snn.json')
        
        if load_snn_agent(snn_ctx, filepath):
            print(f"Loaded agent {agent_id} from {filepath}")
            count += 1
        else:
            print(f"Failed to load agent {agent_id} from {filepath}")
    
    return count
