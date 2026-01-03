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
    runner = getattr(exp_def, 'runner', None)
    
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
        if snn_domain.tensors.get('use_vectorized_queue', False):
             # Buffer is (Time, N) tensor
             total_spike_queue += np.count_nonzero(snn_domain.tensors['spike_buffer'])
        else:
             total_spike_queue += sum(len(v) for v in snn_domain.spike_queue.values())
    
    metrics['debug_total_synapses'] = total_synapses
    metrics['debug_spike_queue_size'] = total_spike_queue

    # 4. Explicit GC (Optional optimization, arguably belongs here or in execution)
    # Keeping it here as it relates to memory metric hygiene? 
    # Or maybe strictly in execution. Let's keep it here for now as it was part of the metric block.
    # Actually, GC is a side effect. Let's leave it out or put in runner. 
    # The original code had it in the metric block.
    # Clean split: This process should essentially be PURE CALCULATION.
    # GC is side effect. Let's move GC to p_episode_runner or a cleanup process.
    # I will OMIT GC from here.
