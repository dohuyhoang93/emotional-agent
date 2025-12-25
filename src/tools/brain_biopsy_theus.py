"""
Brain Biopsy Tool - Theus Version
==================================
Công cụ debugging và analysis cho SNN trong Theus framework.

Features:
- Inspect neurons và synapses
- Analyze sensor learning (16-dim vectors)
- Detect causality learning (switch → gate)
- Compare before/after training

Author: Do Huy Hoang
Date: 2025-12-25
"""
import json
import numpy as np
from typing import Dict, Any, List, Tuple
from src.core.snn_context_theus import SNNSystemContext, NeuronState, SynapseState


class BrainBiopsyTheus:
    """
    Brain Biopsy cho Theus SNN.
    
    Công cụ "sinh thiết não" để debug và analyze SNN.
    """
    
    @staticmethod
    def inspect_neuron(
        snn_ctx: SNNSystemContext,
        neuron_id: int
    ) -> Dict[str, Any]:
        """
        Inspect chi tiết 1 neuron.
        
        Args:
            snn_ctx: SNN system context
            neuron_id: Neuron ID
            
        Returns:
            Dict chứa thông tin neuron
        """
        if neuron_id >= len(snn_ctx.domain_ctx.neurons):
            return {"error": f"Neuron ID {neuron_id} not found"}
        
        neuron = snn_ctx.domain_ctx.neurons[neuron_id]
        
        # Tìm synapses liên quan
        incoming = [
            {
                'id': s.synapse_id,
                'from': s.pre_neuron_id,
                'weight': float(s.weight),
                'commit': s.commit_state,
            }
            for s in snn_ctx.domain_ctx.synapses
            if s.post_neuron_id == neuron_id
        ]
        
        outgoing = [
            {
                'id': s.synapse_id,
                'to': s.post_neuron_id,
                'weight': float(s.weight),
                'commit': s.commit_state,
            }
            for s in snn_ctx.domain_ctx.synapses
            if s.pre_neuron_id == neuron_id
        ]
        
        return {
            'neuron_id': neuron.neuron_id,
            'state': {
                'potential': float(neuron.potential),
                'threshold': float(neuron.threshold),
                'fire_count': neuron.fire_count,
            },
            'vectors': {
                'prototype': neuron.prototype_vector.tolist(),
                'prototype_norm': float(np.linalg.norm(neuron.prototype_vector)),
            },
            'connectivity': {
                'incoming_count': len(incoming),
                'outgoing_count': len(outgoing),
                'incoming_top5': incoming[:5],
                'outgoing_top5': outgoing[:5],
            },
        }
    
    @staticmethod
    def inspect_population(
        snn_ctx: SNNSystemContext
    ) -> Dict[str, Any]:
        """
        Inspect toàn bộ population.
        
        Args:
            snn_ctx: SNN system context
            
        Returns:
            Dict chứa population stats
        """
        neurons = snn_ctx.domain_ctx.neurons
        synapses = snn_ctx.domain_ctx.synapses
        
        # Neuron stats
        active_neurons = sum(1 for n in neurons if n.fire_count > 0)
        
        # Synapse stats by commit state
        fluid_synapses = sum(1 for s in synapses if s.commit_state == 0)
        solid_synapses = sum(1 for s in synapses if s.commit_state == 1)
        revoked_synapses = sum(1 for s in synapses if s.commit_state == 2)
        
        # Weight distribution
        weights = [s.weight for s in synapses]
        avg_weight = np.mean(weights) if weights else 0.0
        max_weight = np.max(weights) if weights else 0.0
        
        return {
            'population': {
                'total_neurons': len(neurons),
                'active_neurons': active_neurons,
                'inactive_neurons': len(neurons) - active_neurons,
            },
            'connectivity': {
                'total_synapses': len(synapses),
                'fluid_synapses': fluid_synapses,
                'solid_synapses': solid_synapses,
                'revoked_synapses': revoked_synapses,
            },
            'weights': {
                'avg': float(avg_weight),
                'max': float(max_weight),
            },
            'time': snn_ctx.domain_ctx.current_time,
        }
    
    @staticmethod
    def inspect_sensor_learning(
        snn_ctx: SNNSystemContext,
        sensor_vector: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze xem neurons học được gì từ sensor vector 16-dim.
        
        Args:
            snn_ctx: SNN system context
            sensor_vector: Current sensor vector (16-dim)
            
        Returns:
            Dict chứa sensor learning analysis
        """
        neurons = snn_ctx.domain_ctx.neurons
        
        # Tính similarity giữa sensor và prototype vectors
        similarities = []
        for neuron in neurons:
            sim = np.dot(sensor_vector, neuron.prototype_vector)
            similarities.append({
                'neuron_id': neuron.neuron_id,
                'similarity': float(sim),
                'fire_count': neuron.fire_count,
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Phân tích kênh nào được học nhiều nhất
        channel_activations = np.zeros(16)
        for neuron in neurons:
            if neuron.fire_count > 0:
                # Neurons active → prototype của chúng đại diện cho patterns đã học
                channel_activations += np.abs(neuron.prototype_vector)
        
        channel_activations /= max(1, sum(1 for n in neurons if n.fire_count > 0))
        
        return {
            'top_matching_neurons': similarities[:10],
            'channel_learning': {
                f'channel_{i}': float(channel_activations[i])
                for i in range(16)
            },
            'interpretation': {
                'channel_0_1': 'Position (proprioception)',
                'channel_2_9': 'Tactile (8 directions)',
                'channel_10_11': 'Auditory (events)',
                'channel_12_15': 'Reserved',
            }
        }
    
    @staticmethod
    def inspect_causality(
        snn_ctx: SNNSystemContext,
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Detect causality learning: switch → gate relationships.
        
        Tìm synapses mạnh (weight > threshold) có thể đại diện cho
        quan hệ nhân quả đã học được.
        
        Args:
            snn_ctx: SNN system context
            threshold: Weight threshold để coi là "learned"
            
        Returns:
            Dict chứa causality analysis
        """
        synapses = snn_ctx.domain_ctx.synapses
        
        # Tìm strong synapses
        strong_synapses = [
            {
                'synapse_id': s.synapse_id,
                'from': s.pre_neuron_id,
                'to': s.post_neuron_id,
                'weight': float(s.weight),
                'commit': s.commit_state,
                'fitness': float(s.fitness),
            }
            for s in synapses
            if s.weight > threshold
        ]
        
        # Sort by weight
        strong_synapses.sort(key=lambda x: x['weight'], reverse=True)
        
        # Phân tích patterns
        # Neurons 0-15 là input (sensor)
        # Neurons 16+ là hidden/output
        
        sensor_to_hidden = [
            s for s in strong_synapses
            if s['from'] < 16 and s['to'] >= 16
        ]
        
        hidden_to_hidden = [
            s for s in strong_synapses
            if s['from'] >= 16 and s['to'] >= 16
        ]
        
        return {
            'strong_synapses_count': len(strong_synapses),
            'top_10_strongest': strong_synapses[:10],
            'patterns': {
                'sensor_to_hidden': len(sensor_to_hidden),
                'hidden_to_hidden': len(hidden_to_hidden),
            },
            'causality_candidates': sensor_to_hidden[:5],  # Top 5 có thể là causality
        }
    
    @staticmethod
    def compare_before_after(
        before_ctx: SNNSystemContext,
        after_ctx: SNNSystemContext
    ) -> Dict[str, Any]:
        """
        So sánh SNN trước và sau training.
        
        Args:
            before_ctx: SNN context trước training
            after_ctx: SNN context sau training
            
        Returns:
            Dict chứa comparison
        """
        # Weight changes
        before_weights = [s.weight for s in before_ctx.domain_ctx.synapses]
        after_weights = [s.weight for s in after_ctx.domain_ctx.synapses]
        
        weight_delta = np.array(after_weights) - np.array(before_weights)
        
        # Prototype changes
        before_protos = [n.prototype_vector for n in before_ctx.domain_ctx.neurons]
        after_protos = [n.prototype_vector for n in after_ctx.domain_ctx.neurons]
        
        proto_distances = [
            float(np.linalg.norm(after - before))
            for before, after in zip(before_protos, after_protos)
        ]
        
        # Commit state changes
        before_solid = sum(1 for s in before_ctx.domain_ctx.synapses if s.commit_state == 1)
        after_solid = sum(1 for s in after_ctx.domain_ctx.synapses if s.commit_state == 1)
        
        return {
            'weight_changes': {
                'mean_delta': float(np.mean(weight_delta)),
                'max_increase': float(np.max(weight_delta)),
                'max_decrease': float(np.min(weight_delta)),
                'std': float(np.std(weight_delta)),
            },
            'prototype_changes': {
                'mean_distance': float(np.mean(proto_distances)),
                'max_distance': float(np.max(proto_distances)),
                'neurons_changed': sum(1 for d in proto_distances if d > 0.1),
            },
            'commitment': {
                'before_solid': before_solid,
                'after_solid': after_solid,
                'new_solid': after_solid - before_solid,
            },
        }
    
    @staticmethod
    def export_to_json(data: Dict[str, Any], filename: str):
        """Export data to JSON file."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Exported to {filename}")


# ============================================================================
# Demo Functions
# ============================================================================

def demo_basic_inspection():
    """Demo basic inspection."""
    from src.core.snn_context_theus import SNNGlobalContext, SNNDomainContext, NeuronState, SynapseState
    
    print("=" * 60)
    print("DEMO: BASIC INSPECTION")
    print("=" * 60)
    
    # Create SNN
    global_ctx = SNNGlobalContext(num_neurons=50, vector_dim=16, connectivity=0.15, seed=42)
    domain_ctx = SNNDomainContext(global_ctx)
    
    # Create neurons
    for i in range(50):
        neuron = NeuronState(
            neuron_id=i,
            prototype_vector=np.random.randn(16).astype(np.float32),
            threshold=1.0
        )
        domain_ctx.neurons.append(neuron)
    
    # Create synapses
    np.random.seed(42)
    synapse_id = 0
    for pre in range(50):
        for post in range(50):
            if pre != post and np.random.rand() < 0.15:
                synapse = SynapseState(
                    synapse_id=synapse_id,
                    pre_neuron_id=pre,
                    post_neuron_id=post,
                    weight=np.random.rand()
                )
                domain_ctx.synapses.append(synapse)
                synapse_id += 1
    
    snn_ctx = SNNSystemContext(global_ctx, domain_ctx)
    
    # Inspect
    print("\n1. INSPECT NEURON 0:")
    neuron_info = BrainBiopsyTheus.inspect_neuron(snn_ctx, 0)
    print(json.dumps(neuron_info, indent=2))
    
    print("\n2. INSPECT POPULATION:")
    pop_info = BrainBiopsyTheus.inspect_population(snn_ctx)
    print(json.dumps(pop_info, indent=2))
    
    print("\n3. INSPECT SENSOR LEARNING:")
    sensor_vec = np.random.rand(16).astype(np.float32)
    sensor_info = BrainBiopsyTheus.inspect_sensor_learning(snn_ctx, sensor_vec)
    print(json.dumps(sensor_info, indent=2))
    
    print("\n4. INSPECT CAUSALITY:")
    causality_info = BrainBiopsyTheus.inspect_causality(snn_ctx, threshold=0.7)
    print(json.dumps(causality_info, indent=2))


if __name__ == '__main__':
    demo_basic_inspection()
