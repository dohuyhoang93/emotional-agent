"""
Demo Brain Biopsy Tool
=======================
Demonstrate BrainBiopsyTheus capabilities với fresh SNN.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import json
import numpy as np
from src.tools.brain_biopsy_theus import BrainBiopsyTheus
from src.core.snn_context_theus import create_snn_context_theus

def main():
    print("=" * 70)
    print("BRAIN BIOPSY DEMO")
    print("=" * 70)
    print()
    
    # Create fresh SNN
    print("Creating SNN (50 neurons, 16-dim vectors)...")
    snn_ctx = create_snn_context_theus(
        num_neurons=50,
        connectivity=0.15,
        vector_dim=16,
        seed=42
    )
    print(f"✅ Created {len(snn_ctx.domain_ctx.neurons)} neurons")
    print(f"✅ Created {len(snn_ctx.domain_ctx.synapses)} synapses")
    print()
    
    # Inspect population
    print("-" * 70)
    print("1. POPULATION ANALYSIS")
    print("-" * 70)
    pop_report = BrainBiopsyTheus.inspect_population(snn_ctx)
    print(json.dumps(pop_report, indent=2))
    print()
    
    # Inspect specific neuron
    print("-" * 70)
    print("2. NEURON #0 DETAIL")
    print("-" * 70)
    neuron_report = BrainBiopsyTheus.inspect_neuron(snn_ctx, 0)
    print(json.dumps(neuron_report, indent=2))
    print()
    
    # Sensor learning analysis
    print("-" * 70)
    print("3. SENSOR LEARNING (Input Neurons 0-15)")
    print("-" * 70)
    # Create test sensor vector
    test_sensor = np.random.rand(16)
    test_sensor = test_sensor / np.linalg.norm(test_sensor)
    sensor_report = BrainBiopsyTheus.inspect_sensor_learning(snn_ctx, test_sensor)
    print(json.dumps(sensor_report, indent=2))
    print()
    
    # Simulate some activity
    print("-" * 70)
    print("4. SIMULATING ACTIVITY")
    print("-" * 70)
    
    # Inject test pattern
    test_pattern = np.random.rand(16)
    test_pattern = test_pattern / np.linalg.norm(test_pattern)
    
    print(f"Injecting test pattern: {test_pattern[:4]}... (first 4 dims)")
    
    # Set input neuron potentials
    for i in range(16):
        snn_ctx.domain_ctx.neurons[i].potential = test_pattern[i] * 5.0
        snn_ctx.domain_ctx.neurons[i].potential_vector = test_pattern
    
    # Fire some neurons
    fired = []
    for i in range(16):
        if snn_ctx.domain_ctx.neurons[i].potential >= snn_ctx.domain_ctx.neurons[i].threshold:
            snn_ctx.domain_ctx.neurons[i].fire_count += 1
            snn_ctx.domain_ctx.neurons[i].last_fire_time = 1
            fired.append(i)
    
    print(f"✅ {len(fired)} neurons fired: {fired}")
    print()
    
    # Re-inspect population
    print("-" * 70)
    print("5. POPULATION AFTER ACTIVITY")
    print("-" * 70)
    pop_report_after = BrainBiopsyTheus.inspect_population(snn_ctx)
    print(json.dumps(pop_report_after, indent=2))
    print()
    
    print("=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
    print()
    print("Brain Biopsy Tool có thể:")
    print("  ✅ Inspect toàn bộ population (stats, fire rates)")
    print("  ✅ Analyze từng neuron (potential, connections, vectors)")
    print("  ✅ Monitor sensor learning (input neurons)")
    print("  ✅ Detect causality patterns (switch → gate)")
    print("  ✅ Compare before/after training")
    print()
    print("Để sử dụng trong experiment:")
    print("  1. Save SNN state sau mỗi episode")
    print("  2. Load state tại checkpoints")
    print("  3. Run biopsy analysis")
    print("  4. Export reports to JSON")
    print()

if __name__ == "__main__":
    main()
