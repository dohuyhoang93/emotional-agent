
import numpy as np
from dataclasses import dataclass
from typing import List

# Mock Classes to simulate Context
class MockNeuron:
    def __init__(self, vector, fire_count):
        self.prototype_vector = np.array(vector, dtype=float)
        self.fire_count = fire_count

@dataclass
class MockDomainContext:
    neurons: List[MockNeuron]
    snn_emotion_vector = None
    # We will inject current_observation manually

@dataclass
class MockSNNContext:
    domain_ctx: MockDomainContext

@dataclass
class MockSystemContext:
    domain_ctx: object

class MockRootDomain:
    def __init__(self):
        self.snn_context = None
        self.current_observation = None
        self.snn_emotion_vector = None
        self.previous_snn_emotion_vector = None

# Re-implement the logic specifically (or import if possible, but import is hard with mocks)
# To strictly verify the *logic* implemented, we can copy the snippet or try to import it.
# Since the logic is embedded in a function, we will import the module and mock the input ctx.
# However, importing 'src' might be tricky depending on python path. 
# We'll try to import sys path.

import sys
import os
sys.path.append(os.getcwd())

from src.processes.snn_rl_bridge import _encode_emotion_vector_impl 

def test_bridge_attention():
    print("Testing Bridge Attention Logic...")
    
    # Setup Context
    root_domain = MockRootDomain()
    snn_domain = MockDomainContext(neurons=[])
    root_domain.snn_context = MockSNNContext(domain_ctx=snn_domain)
    
    ctx = MockSystemContext(domain_ctx=root_domain)

    # SCENARIO 1: Fear Query vs Mixed Neurons
    # Query: [1, 0] (Simplified 2D for mental model, actual is 16D)
    # Neuron A: [1, 0] (Fear - Aligned) -> Score 1.0 -> Sigmoid(1.0) ~= 0.73
    # Neuron B: [-1, 0] (Anti-Fear - Opposed) -> Score -1.0 -> Sigmoid(-1.0) ~= 0.27
    
    # Setup 16D vectors
    query_vec = np.zeros(16)
    query_vec[0] = 1.0 # "Fear" dimension
    
    neuron_a_vec = np.zeros(16)
    neuron_a_vec[0] = 1.0
    
    neuron_b_vec = np.zeros(16)
    neuron_b_vec[0] = -1.0
    
    # Set Observation
    root_domain.current_observation = query_vec
    
    # Set Neurons (Both Active)
    snn_domain.neurons = [
        MockNeuron(neuron_a_vec, fire_count=1),
        MockNeuron(neuron_b_vec, fire_count=1)
    ]
    
    # Execute
    _encode_emotion_vector_impl(ctx)
    result = root_domain.snn_emotion_vector.numpy()
    
    print(f"Result Vector: {result[:2]}...") # Look at first dimension
    
    # EXPECTATION:
    # Mean would be (1 + -1)/2 = 0.
    # Attention:
    # Gate A = Sigmoid(1) = 0.731
    # Gate B = Sigmoid(-1) = 0.268
    # Weighted Sum = (0.731 * 1) + (0.268 * -1) = 0.731 - 0.268 = 0.463
    # Normalized -> 1.0
    
    # Wait, normalization makes it 1.0 anyway if it's the only non-zero dimension.
    # Let's verify the SIGN is positive (Fear preserved).
    
    if result[0] > 0.9: # Should be normalized to near 1.0
        print("PASS: Fear dominance preserved (Positive result).")
    else:
        print(f"FAIL: Result {result[0]} is not dominant.")
        
    # SCENARIO 2: Orthogonal Query
    # Query: [0, 1] (Curiosity)
    # Neuron A: [1, 0] (Fear) -> Score 0 -> Sigmoid(0) = 0.5
    # Neuron B: [-1, 0] (Anti-Fear) -> Score 0 -> Sigmoid(0) = 0.5
    # Sum: 0.5*1 + 0.5*-1 = 0.
    
    query_vec_2 = np.zeros(16)
    query_vec_2[1] = 1.0
    root_domain.current_observation = query_vec_2
    
    _encode_emotion_vector_impl(ctx)
    result_2 = root_domain.snn_emotion_vector.numpy()
    
    print(f"Orthogonal Result: {result_2[:2]}")
    # Should be 0 in dim 0.
    if abs(result_2[0]) < 0.001:
         print("PASS: Irrelevant emotions canceled out.")
    else:
         print("FAIL: Orthogonal query should not bias dimension 0.")

    print("Bridge Attention Verification Complete.")

if __name__ == "__main__":
    test_bridge_attention()
