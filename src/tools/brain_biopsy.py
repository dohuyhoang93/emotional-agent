"""
Brain Biopsy Tool: Entity Inspector for ECS Debugging
======================================================
Công cụ để "lắp ráp" view từ các mảng ECS phân tán.
"""
from src.core.snn_context import SNNContext, NeuronRecord, SynapseRecord
from typing import Dict, Any, List
import json


class BrainBiopsy:
    """
    Công cụ sinh thiết não - Inspect entities trong ECS.
    """
    
    @staticmethod
    def inspect_neuron(ctx: SNNContext, neuron_id: int) -> Dict[str, Any]:
        """
        Lắp ráp toàn bộ thông tin của một neuron từ các mảng ECS.
        
        Returns:
            Dict chứa tất cả thông tin về neuron (như một "Virtual Object")
        """
        if neuron_id >= len(ctx.neurons):
            return {"error": f"Neuron ID {neuron_id} not found"}
        
        neuron = ctx.neurons[neuron_id]
        
        # Tìm tất cả synapses liên quan
        incoming_synapses = [
            {
                'id': s.synapse_id,
                'from': s.pre_neuron_id,
                'weight': s.weight,
                'type': s.synapse_type,
                'confidence': s.confidence
            }
            for s in ctx.synapses if s.post_neuron_id == neuron_id
        ]
        
        outgoing_synapses = [
            {
                'id': s.synapse_id,
                'to': s.post_neuron_id,
                'weight': s.weight,
                'type': s.synapse_type,
                'confidence': s.confidence
            }
            for s in ctx.synapses if s.pre_neuron_id == neuron_id
        ]
        
        # Lắp ráp Virtual Object
        return {
            'neuron_id': neuron.neuron_id,
            'state': {
                'potential': neuron.potential,
                'threshold': neuron.threshold,
                'last_fire_time': neuron.last_fire_time,
                'fire_count': neuron.fire_count,
            },
            'vector': {
                'potential_vector': neuron.potential_vector.tolist(),
                'prototype_vector': neuron.prototype_vector.tolist(),
            },
            'connectivity': {
                'incoming_count': len(incoming_synapses),
                'outgoing_count': len(outgoing_synapses),
                'incoming': incoming_synapses[:5],  # Top 5
                'outgoing': outgoing_synapses[:5],
            },
            'health': {
                'is_active': (ctx.current_time - neuron.last_fire_time) < 100,
                'firing_rate': neuron.fire_count / max(1, ctx.current_time),
            }
        }
    
    @staticmethod
    def inspect_population(ctx: SNNContext) -> Dict[str, Any]:
        """
        Tổng quan về toàn bộ quần thể neuron.
        """
        total_neurons = len(ctx.neurons)
        total_synapses = len(ctx.synapses)
        
        # Phân loại synapses
        native_count = sum(1 for s in ctx.synapses if s.synapse_type == "native")
        shadow_count = sum(1 for s in ctx.synapses if s.synapse_type == "shadow")
        
        # Tính firing rate distribution
        # NOTE: Neurons bị kill có threshold rất cao (999)
        active_neurons = sum(
            1 for n in ctx.neurons 
            if (ctx.current_time - n.last_fire_time) < 100 and n.threshold < 10.0
        )
        
        killed_neurons = sum(1 for n in ctx.neurons if n.threshold > 10.0)
        
        # DEBUG: Kiểm tra last_fire_time
        alive_neurons = [n for n in ctx.neurons if n.threshold < 10.0]
        if alive_neurons:
            recent_fires = [(i, ctx.current_time - n.last_fire_time) 
                           for i, n in enumerate(ctx.neurons) 
                           if n.threshold < 10.0 and (ctx.current_time - n.last_fire_time) < 200]
            if recent_fires:
                print(f"[DEBUG] Recent fires (last 200ms): {len(recent_fires)} neurons")
                print(f"[DEBUG] Sample: {recent_fires[:5]}")
        
        return {
            'population': {
                'total_neurons': total_neurons,
                'active_neurons': active_neurons,
                'killed_neurons': killed_neurons,
                'inactive_neurons': total_neurons - active_neurons - killed_neurons,
            },
            'connectivity': {
                'total_synapses': total_synapses,
                'native_synapses': native_count,
                'shadow_synapses': shadow_count,
                'avg_synapses_per_neuron': total_synapses / max(1, total_neurons),
            },
            'metrics': ctx.metrics,
            'social': ctx.social_signals,
            'time': ctx.current_time,
        }
    
    @staticmethod
    def export_to_json(data: Dict[str, Any], filename: str):
        """Xuất dữ liệu ra file JSON để phân tích."""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Exported to {filename}")


def demo_biopsy():
    """Demo Brain Biopsy Tool."""
    from src.core.snn_context import create_snn_context
    
    ctx = create_snn_context(num_neurons=10, connectivity=0.3)
    ctx.current_time = 100
    
    # Inspect một neuron cụ thể
    neuron_info = BrainBiopsy.inspect_neuron(ctx, neuron_id=0)
    print("=== NEURON 0 INSPECTION ===")
    print(json.dumps(neuron_info, indent=2))
    
    # Inspect toàn bộ quần thể
    pop_info = BrainBiopsy.inspect_population(ctx)
    print("\n=== POPULATION OVERVIEW ===")
    print(json.dumps(pop_info, indent=2))


if __name__ == '__main__':
    demo_biopsy()
