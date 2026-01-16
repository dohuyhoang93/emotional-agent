from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
import numpy as np

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.metrics'],
    outputs=['domain', 'domain_ctx', 'domain.metrics'],
    side_effects=[],
    errors=[]
)
def enrich_episode_metrics(ctx: OrchestratorSystemContext):
    """
    Process: Calculate and enrich the 'metrics' dictionary with SNN and RL statistics.
    Decoupled from execution logic for better SRP.
    """
    domain = ctx.domain_ctx
    metrics = domain.metrics
    
    # Get Runner
    exp_def = domain.experiments[domain.active_experiment_idx]
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_def.name)
    
    if not runner or not runner.coordinator.agents:
        return

    # 1. Maturity (Epsilon) from Agent 0
    agent0 = runner.coordinator.agents[0]
    epsilon = getattr(agent0.domain_ctx, 'current_exploration_rate', 0.0)
    metrics['epsilon'] = epsilon
    metrics['maturity'] = (1.0 - epsilon) * 100.0

    # 2. SNN Firing Rate (Average across population)
    avg_fr = 0.0
    count = 0
    for agent in runner.coordinator.agents:
        snn_domain = agent.snn_ctx.domain_ctx
        if 'avg_firing_rate' in snn_domain.metrics:
             avg_fr += snn_domain.metrics['avg_firing_rate']
        count += 1
    
    if count > 0:
        metrics['avg_firing_rate'] = avg_fr / count
    else:
        metrics['avg_firing_rate'] = 0.0

    # 3. DEBUG: Memory Leak Diagnosis (Synapse Count & Spike Queue)
    total_synapses = 0
    total_spike_queue = 0
    for agent in runner.coordinator.agents:
        snn_domain = agent.snn_ctx.domain_ctx
        total_synapses += len(snn_domain.synapses)
        
        # Check buffer type (Vectorized vs Dict)
        if snn_domain.heavy_tensors.get('use_vectorized_queue', False):
             # Buffer is (Time, N) tensor
             total_spike_queue += np.count_nonzero(snn_domain.heavy_tensors['spike_buffer'])
        else:
             total_spike_queue += sum(len(v) for v in snn_domain.spike_queue.values())
    
    metrics['debug_total_synapses'] = total_synapses
    metrics['debug_spike_queue_size'] = total_spike_queue
    
    # 4. DEBUG: Q-Table Size (Memory Leak Investigation)
    total_q_table_entries = 0
    for agent in runner.coordinator.agents:
        rl_domain = agent.domain_ctx
        if hasattr(rl_domain, 'heavy_q_table'):
            total_q_table_entries += len(rl_domain.heavy_q_table)
    metrics['debug_q_table_size'] = total_q_table_entries

    # 5. DEBUG: PyTorch Tensor Count & Process Memory
    import gc
    import torch
    import psutil
    import os
    from collections import Counter
    
    # Count PyTorch tensors in memory AND analyze shapes
    tensor_count = 0
    tensor_memory = 0
    shape_counter = Counter()
    grad_tensor_count = 0
    
    for obj in gc.get_objects():
        try:
            if torch.is_tensor(obj):
                tensor_count += 1
                tensor_memory += obj.element_size() * obj.nelement()
                shape_counter[str(tuple(obj.shape))] += 1
                if obj.requires_grad or obj.grad_fn is not None:
                    grad_tensor_count += 1
        except:
            pass
    
    metrics['debug_torch_tensor_count'] = tensor_count
    metrics['debug_torch_tensor_mb'] = round(tensor_memory / 1024 / 1024, 2)
    metrics['debug_torch_grad_tensors'] = grad_tensor_count
    
    # Top 5 tensor shapes (for leak identification)
    top_shapes = shape_counter.most_common(5)
    metrics['debug_top_tensor_shapes'] = {shape: count for shape, count in top_shapes}
    
    # 7. DEBUG: Referrer Analysis for Leaking Shape (16,)
    # Only run this if we have many (16,) tensors to avoid spam
    leak_shape = "(16,)"
    if shape_counter[leak_shape] > 2000:
        found_ref = False
        # Find one sample tensor of this shape
        for obj in gc.get_objects():
            if not found_ref and torch.is_tensor(obj) and str(tuple(obj.shape)) == leak_shape:
                try:
                    refs = gc.get_referrers(obj)
                    for r in refs:
                        # We are looking for the DICT that holds this tensor
                        if isinstance(r, dict) and 'agent_id' in r and 'position' in r:
                             # FOUND THE DICT! Now find who holds this dict (The LIST)
                             dict_refs = gc.get_referrers(r)
                             metrics['debug_leak_dict_keys'] = list(r.keys())
                             
                             for dr in dict_refs:
                                 if isinstance(dr, list) and len(dr) > 1000:
                                     # FOUND THE LIST!
                                     metrics['debug_leak_list_len'] = len(dr)
                                     metrics['debug_leak_list_sample_types'] = [type(x).__name__ for x in dr[:5]]
                                     
                                     # WHO HOLDS THE LIST?
                                     list_refs = gc.get_referrers(dr)
                                     list_ref_info = []
                                     for lr in list_refs:
                                         tname = type(lr).__name__
                                         if tname == 'function':
                                             list_ref_info.append(f"function({lr.__name__})")
                                         elif tname == 'frame':
                                             list_ref_info.append(f"frame({lr.f_code.co_name}:{lr.f_lineno})")
                                         elif hasattr(lr, '__class__'):
                                              list_ref_info.append(f"obj({lr.__class__.__name__})")
                                         else:
                                             list_ref_info.append(tname)
                                     
                                     metrics['debug_leak_list_owners'] = list_ref_info[:5]
                                     found_ref = True
                                     break
                        if found_ref: break
                except:
                    pass
            if found_ref: break


    # Process memory (RSS)
    process = psutil.Process(os.getpid())
    metrics['debug_process_memory_mb'] = round(process.memory_info().rss / 1024 / 1024, 2)



    # 6. Explicit GC (Optional optimization, arguably belongs here or in execution)
    # Keeping it here as it relates to memory metric hygiene? 
    # Or maybe strictly in execution. Let's keep it here for now as it was part of the metric block.
    # Actually, GC is a side effect. Let's leave it out or put in runner. 
    # The original code had it in the metric block.
    # Clean split: This process should essentially be PURE CALCULATION.
    # GC is side effect. Let's move GC to p_episode_runner or a cleanup process.
    # I will OMIT GC from here.

