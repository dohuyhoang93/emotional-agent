from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
import numpy as np

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.metrics'],
    outputs=['domain.metrics'],
    side_effects=[],
    errors=[]
)
def enrich_episode_metrics(ctx: OrchestratorSystemContext):
    """
    Process: Calculate and enrich the 'metrics' dictionary with SNN and RL statistics.
    Decoupled from execution logic for better SRP.
    """
    metrics = getattr(ctx.domain, 'metrics', {})
    # print(f"DEBUG enrich_episode_metrics: metrics type={type(metrics)}, value={metrics}")
    
    # Get experiment info
    active_idx = getattr(ctx.domain, 'active_experiment_idx', 0)
    experiments = getattr(ctx.domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {}
    
    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown')
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if not runner or not runner.coordinator.agents:
        return {}

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
        
        # Thay vì đọc queue hiện tại (đang bằng 0 vì ở cuối episode),
        # ta lấy tổng số gai đã bắn tích lũy trong episode và reset nó cho episode sau
        tracked_spikes = snn_domain.metrics.get('episode_total_spikes', 0)
        total_spike_queue += tracked_spikes
        snn_domain.metrics['episode_total_spikes'] = 0
    
    metrics['debug_total_synapses'] = total_synapses
    metrics['debug_spike_queue_size'] = total_spike_queue
    
    # 4. Neural Brain Metrics (V3 Migration)
    total_q_table_entries = 0
    neural_loss_avg = 0.0
    neural_q_avg = 0.0
    count_rl = 0
    
    for agent in runner.coordinator.agents:
        rl_domain = agent.domain_ctx
        if hasattr(rl_domain, 'heavy_q_table'):
            total_q_table_entries += len(rl_domain.heavy_q_table)
            
        if 'neural_loss' in rl_domain.metrics:
            neural_loss_avg += rl_domain.metrics['neural_loss']
            neural_q_avg += rl_domain.metrics.get('avg_q_predicted', 0.0)
            count_rl += 1
            
    metrics['debug_q_table_size'] = total_q_table_entries
    if count_rl > 0:
        metrics['neural_loss_avg'] = neural_loss_avg / count_rl
        metrics['avg_q_predicted'] = neural_q_avg / count_rl

    # 5. DEBUG: PyTorch Tensor Count & Process Memory
    import gc
    import torch
    import psutil
    import os
    from collections import Counter
    
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

    # Process memory (RSS)
    process = psutil.Process(os.getpid())
    metrics['debug_process_memory_mb'] = round(process.memory_info().rss / 1024 / 1024, 2)
    
    return {
        'domain.metrics': metrics
    }
