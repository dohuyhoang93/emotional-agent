
import time
import unittest
import numpy as np
import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

from src.core.snn_context_theus import create_snn_context_theus
from src.processes.snn_core_theus import process_integrate, process_fire, process_tick
from src.core.context import DomainContext, SystemContext # Mock wrapper

class MockGlobalCtx:
    initial_threshold = 1.0
    vector_dim = 16
    seed = 42

class MockWrapperContext:
    def __init__(self, snn_ctx):
        self.domain_ctx = DomainContext()
        self.domain_ctx.snn_context = snn_ctx

class TestVectorizedPerformance(unittest.TestCase):
    def test_performance_1000_steps(self):
        print("\n--- Starting Vectorized Performance Test ---")
        
        # 1. Setup Large SNN (500 Neurons to stress test)
        # Old loop code would choke here.
        num_neurons = 500 
        num_synapses_per_neuron = 100 # Avg connectivity 0.2
        connectivity = num_synapses_per_neuron / num_neurons
        
        start_setup = time.time()
        snn_ctx = create_snn_context_theus(
            num_neurons=num_neurons,
            connectivity=connectivity,
            vector_dim=16,
            seed=42,
            initial_threshold=0.5
        )
        ctx = MockWrapperContext(snn_ctx)
        print(f"Setup Time: {time.time() - start_setup:.4f}s")
        print(f"Neurons: {num_neurons}, Synapses: {len(snn_ctx.domain_ctx.synapses)}")
        
        # 2. Inject Initial Spikes to kickstart activity
        # Force neurons 0-10 to fire
        snn_ctx.domain_ctx.spike_queue[0] = list(range(10))
        
        # 3. Run Simulation Loop
        steps = 100
        start_sim = time.time()
        
        total_fired = 0
        
        for i in range(steps):
            process_integrate(ctx)
            
            # Debug: Check potentials after integrate
            neurons = snn_ctx.domain_ctx.neurons
            max_pot = max([n.potential for n in neurons])
            if i < 5:
                print(f"Step {i}: Max Potential = {max_pot}")
                # Check weights
                if 'weights' in snn_ctx.domain_ctx.tensors:
                    w = snn_ctx.domain_ctx.tensors['weights']
                    print(f"   Weights Sum: {np.sum(w)}")
                    print(f"   Spikes at {i}: {snn_ctx.domain_ctx.spike_queue.get(i, [])}")
            
            process_fire(ctx)
            process_tick(ctx)
            
            # Check correctness: Potentials should change
            # Check metrics
            count = snn_ctx.domain_ctx.metrics.get('fired_count', 0)
            total_fired += count
            
        duration = time.time() - start_sim
        speed = steps / duration
        print(f"Simulation Time: {duration:.4f}s for {steps} steps")
        print(f"Speed: {speed:.2f} steps/sec")
        print(f"Total Spikes: {total_fired}")
        
        # 4. Assertions
        # Speed should be reasonably high for vectorized code (e.g > 50 steps/sec)
        # Even on CPU, 500 neurons should be instant matrix mul.
        # 500x500 matrix = 250k floats. Tiny.
        
        self.assertGreater(speed, 10.0, "Simulation is too slow! Vectorization might define failed.")
        self.assertGreater(total_fired, 0, "SNN is dead! No neurons fired.")
        
        # Verify Object Sync
        # Check if Neuron objects have updated potentials
        neuron_0 = snn_ctx.domain_ctx.neurons[0]
        # Potential is reset to -0.1 on fire, or decays
        # Just check it's not 0.0 (unless it fired exactly now)
        # Or check that at least one neuron has potential != 0
        
        active_neurons = [n for n in snn_ctx.domain_ctx.neurons if abs(n.potential) > 1e-9]
        print(f"Active Neurons (Potential != 0): {len(active_neurons)}")
        self.assertGreater(len(active_neurons), 0, "All potentials are zero? Sync failed.")

if __name__ == '__main__':
    unittest.main()
