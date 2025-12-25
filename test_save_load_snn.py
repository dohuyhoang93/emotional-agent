"""
Test Save/Load SNN
===================
Test save và load trained SNN agents.
"""
import os
import json
import numpy as np
from src.core.snn_context_theus import SNNSystemContext, SNNGlobalContext, SNNDomainContext
from src.utils.snn_persistence import save_snn_agent, load_snn_agent


def test_save_load():
    """Test save/load cycle."""
    print("=" * 60)
    print("TEST SAVE/LOAD SNN")
    print("=" * 60)
    
    # Create SNN context
    print("\n1. CREATE SNN CONTEXT:")
    global_ctx = SNNGlobalContext(
        num_neurons=50,
        vector_dim=16,
        connectivity=0.15,
        seed=42
    )
    
    domain_ctx = SNNDomainContext(global_ctx)
    
    # Manually create neurons and synapses (since SNNDomainContext doesn't auto-create)
    from src.core.snn_context_theus import NeuronState, SynapseState
    
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
                    weight=0.5
                )
                domain_ctx.synapses.append(synapse)
                synapse_id += 1
    
    snn_ctx = SNNSystemContext(global_ctx, domain_ctx)
    
    print(f"   Neurons: {len(snn_ctx.domain_ctx.neurons)}")
    print(f"   Synapses: {len(snn_ctx.domain_ctx.synapses)}")
    print("   ✅ Context created")
    
    # Modify some values (simulate training)
    print("\n2. SIMULATE TRAINING:")
    original_prototype = snn_ctx.domain_ctx.neurons[0].prototype_vector.copy()
    original_weight = snn_ctx.domain_ctx.synapses[0].weight
    
    snn_ctx.domain_ctx.neurons[0].prototype_vector = np.random.randn(16).astype(np.float32)
    snn_ctx.domain_ctx.neurons[0].threshold = 1.5
    snn_ctx.domain_ctx.synapses[0].weight = 0.8
    snn_ctx.domain_ctx.synapses[0].commit_state = 1  # SOLID
    
    print(f"   Modified neuron 0 prototype: {snn_ctx.domain_ctx.neurons[0].prototype_vector[:3]}...")
    print(f"   Modified neuron 0 threshold: {snn_ctx.domain_ctx.neurons[0].threshold}")
    print(f"   Modified synapse 0 weight: {snn_ctx.domain_ctx.synapses[0].weight}")
    print(f"   Modified synapse 0 commit_state: {snn_ctx.domain_ctx.synapses[0].commit_state}")
    print("   ✅ Training simulated")
    
    # Save
    print("\n3. SAVE SNN:")
    output_dir = "test_save_load"
    filepath = save_snn_agent(snn_ctx, 0, output_dir)
    print(f"   Saved to: {filepath}")
    
    # Verify file exists
    assert os.path.exists(filepath), f"File not found: {filepath}"
    print("   ✅ File exists")
    
    # Check file size
    file_size = os.path.getsize(filepath)
    print(f"   File size: {file_size} bytes")
    assert file_size > 1000, f"File too small: {file_size} bytes"
    print("   ✅ File size OK")
    
    # Reset context (simulate new agent)
    print("\n4. RESET CONTEXT:")
    domain_ctx_new = SNNDomainContext(global_ctx)
    
    # Create neurons and synapses again
    for i in range(50):
        neuron = NeuronState(
            neuron_id=i,
            prototype_vector=np.random.randn(16).astype(np.float32),
            threshold=1.0
        )
        domain_ctx_new.neurons.append(neuron)
    
    np.random.seed(42)
    synapse_id = 0
    for pre in range(50):
        for post in range(50):
            if pre != post and np.random.rand() < 0.15:
                synapse = SynapseState(
                    synapse_id=synapse_id,
                    pre_neuron_id=pre,
                    post_neuron_id=post,
                    weight=0.5
                )
                domain_ctx_new.synapses.append(synapse)
                synapse_id += 1
    
    snn_ctx_new = SNNSystemContext(global_ctx, domain_ctx_new)
    
    print(f"   New neuron 0 prototype: {snn_ctx_new.domain_ctx.neurons[0].prototype_vector[:3]}...")
    print(f"   New neuron 0 threshold: {snn_ctx_new.domain_ctx.neurons[0].threshold}")
    print(f"   New synapse 0 weight: {snn_ctx_new.domain_ctx.synapses[0].weight}")
    print("   ✅ Context reset")
    
    # Load
    print("\n5. LOAD SNN:")
    success = load_snn_agent(snn_ctx_new, filepath)
    assert success, "Load failed"
    print("   ✅ Load successful")
    
    # Verify values
    print("\n6. VERIFY VALUES:")
    loaded_prototype = snn_ctx_new.domain_ctx.neurons[0].prototype_vector
    loaded_threshold = snn_ctx_new.domain_ctx.neurons[0].threshold
    loaded_weight = snn_ctx_new.domain_ctx.synapses[0].weight
    loaded_commit = snn_ctx_new.domain_ctx.synapses[0].commit_state
    
    print(f"   Loaded neuron 0 prototype: {loaded_prototype[:3]}...")
    print(f"   Loaded neuron 0 threshold: {loaded_threshold}")
    print(f"   Loaded synapse 0 weight: {loaded_weight}")
    print(f"   Loaded synapse 0 commit_state: {loaded_commit}")
    
    # Check values match
    assert np.allclose(loaded_prototype, snn_ctx.domain_ctx.neurons[0].prototype_vector), "Prototype mismatch"
    assert abs(loaded_threshold - 1.5) < 0.01, f"Threshold mismatch: {loaded_threshold}"
    assert abs(loaded_weight - 0.8) < 0.01, f"Weight mismatch: {loaded_weight}"
    assert loaded_commit == 1, f"Commit state mismatch: {loaded_commit}"
    
    print("   ✅ All values match!")
    
    # Cleanup
    print("\n7. CLEANUP:")
    os.remove(filepath)
    os.rmdir(output_dir)
    print("   ✅ Cleaned up")
    
    print("\n" + "=" * 60)
    print("✅ TEST HOÀN TẤT!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        test_save_load()
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
