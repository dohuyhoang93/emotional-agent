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
import torch
from typing import Any, List, Optional
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
            'current_time': int(snn_ctx.domain_ctx.current_time), # FIX: Phải lưu thời gian hiện tại
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
        state['memory']['q_table'] = domain.heavy_q_table
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
            'last_fire_time': int(neuron.last_fire_time), # FIX: Phải lưu vết firing cuối
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
    
    # NEW V3: Save Gated Integration Network Weights (.pt)
    if rl_ctx and rl_ctx.domain_ctx.heavy_gated_network is not None:
        net = rl_ctx.domain_ctx.heavy_gated_network
        weights_path = os.path.join(output_dir, f'agent_{agent_id}_net.pt')
        torch.save(net.state_dict(), weights_path)
        # print(f"Saved Neural Brain weights to {weights_path}")
    
    return filepath


def load_snn_agent(
    snn_ctx: SNNSystemContext,
    filepath: str,
    rl_ctx: Optional[Any] = None
) -> bool:
    """
    Load SNN agent từ file JSON.
    V3: Hỗ trợ load trọng số Neural Brain từ file .pt tương ứng.
    
    Args:
        snn_ctx: SNN system context (sẽ được update)
        filepath: Path to saved JSON file
        rl_ctx: Optional RL system context to load network weights
        
    Returns:
        success: True if loaded successfully
    """
    if not os.path.exists(filepath):
        return False
    
    # Load state
    try:
        with open(filepath, 'r') as f:
            state = json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return False
    
    # Verify metadata (Loose check for V3)
    if len(snn_ctx.domain_ctx.neurons) != state['metadata']['num_neurons']:
        print(f"Warning: Neuron count mismatch: {len(snn_ctx.domain_ctx.neurons)} vs {state['metadata']['num_neurons']}")
        # Don't fail immediately, try to restore as many as possible
    
    # Restore SNN level state
    if 'current_time' in state['metadata']:
        snn_ctx.domain_ctx.current_time = state['metadata']['current_time']

    # Restore neurons
    for i, neuron_data in enumerate(state['neurons']):
        if i < len(snn_ctx.domain_ctx.neurons):
            neuron = snn_ctx.domain_ctx.neurons[i]
            neuron.prototype_vector = np.array(neuron_data['prototype_vector'], dtype=np.float32)
            neuron.threshold = neuron_data['threshold']
            neuron.fire_count = neuron_data['fire_count']
            if 'last_fire_time' in neuron_data:
                neuron.last_fire_time = neuron_data['last_fire_time']
    
    # Restore synapses
    for i, synapse_data in enumerate(state['synapses']):
        if i < len(snn_ctx.domain_ctx.synapses):
            synapse = snn_ctx.domain_ctx.synapses[i]
            synapse.weight = synapse_data['weight']
            synapse.commit_state = synapse_data['commit_state']
            synapse.consecutive_correct = synapse_data['consecutive_correct']
            synapse.consecutive_wrong = synapse_data['consecutive_wrong']
            synapse.fitness = synapse_data['fitness']
            
    # NEW V3: Load Neural Brain Weights (.pt)
    if rl_ctx and rl_ctx.domain_ctx.heavy_gated_network is not None:
        # Construct path from JSON path: agent_0_snn.json -> agent_0_net.pt
        weights_path = filepath.replace('_snn.json', '_net.pt')
        if os.path.exists(weights_path):
            try:
                state_dict = torch.load(weights_path, map_location='cpu')
                rl_ctx.domain_ctx.heavy_gated_network.load_state_dict(state_dict)
                # print(f"Successfully loaded Neural Brain weights from {weights_path}")
            except Exception as e:
                print(f"Warning: Failed to load Neural weights: {e}")
    
    return True


def save_all_agents(
    agents_snn_contexts: List[SNNSystemContext],
    output_dir: str,
    agents_rl_contexts: Optional[List[Any]] = None
) -> List[str]:
    """
    Lưu tất cả agents.
    V3: Hỗ trợ lưu RL context (Neural Weights) cho từng agent.
    
    Args:
        agents_snn_contexts: List of SNN contexts
        output_dir: Output directory
        agents_rl_contexts: Optional list of RL contexts
        
    Returns:
        filepaths: List of saved filepaths
    """
    filepaths = []
    
    for agent_id, snn_ctx in enumerate(agents_snn_contexts):
        rl_ctx = None
        if agents_rl_contexts and agent_id < len(agents_rl_contexts):
            rl_ctx = agents_rl_contexts[agent_id]
            
        filepath = save_snn_agent(snn_ctx, rl_ctx, agent_id, output_dir)
        filepaths.append(filepath)
        # print(f"Saved agent {agent_id} to {filepath}")
    
    return filepaths


def load_all_agents(
    agents_snn_contexts: List[SNNSystemContext],
    input_dir: str,
    agents_rl_contexts: Optional[List[Any]] = None
) -> int:
    """
    Load tất cả agents.
    V3: Hỗ trợ load RL context (Neural Weights) cho từng agent.
    
    Args:
        agents_snn_contexts: List of SNN contexts (sẽ được update)
        input_dir: Input directory
        agents_rl_contexts: Optional list of RL contexts
        
    Returns:
        count: Number of agents loaded successfully
    """
    count = 0
    
    for agent_id, snn_ctx in enumerate(agents_snn_contexts):
        filepath = os.path.join(input_dir, f'agent_{agent_id}_snn.json')
        
        rl_ctx = None
        if agents_rl_contexts and agent_id < len(agents_rl_contexts):
            rl_ctx = agents_rl_contexts[agent_id]
            
        if load_snn_agent(snn_ctx, filepath, rl_ctx):
            # print(f"Loaded agent {agent_id} from {filepath}")
            count += 1
        else:
            print(f"Failed to load agent {agent_id} from {filepath}")
    
    return count
