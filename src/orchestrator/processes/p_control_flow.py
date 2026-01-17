from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr, set_attr
from src.logger import log
import os
import json
from src.processes.snn_social_learning_theus import process_social_learning_protocol

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=[],  # v2 compatible - no output mapping
    side_effects=[],
    errors=[]
)
def advance_experiment_index(ctx: OrchestratorSystemContext):
    """
    Increments the active experiment index.
    """
    domain, is_dict = get_domain_ctx(ctx)
    current_idx = get_attr(domain, 'active_experiment_idx', 0)
    new_idx = current_idx + 1
    set_attr(domain, 'active_experiment_idx', new_idx)
    log(ctx, "info", f"⏩ Advanced to Experiment Index: {new_idx}")

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.output_dir', 'domain.metrics', 'domain.active_experiment_episode_idx'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def save_metrics_snapshot(ctx: OrchestratorSystemContext):
    """
    DEPRECATED: Saves current metrics to JSON checkpoint.
    
    NOTE: This process is now disabled. Metrics are logged via JSONL only (p_log_metrics.py).
    The legacy metrics.json format is no longer maintained.
    """
    # Legacy JSON snapshot disabled - use metrics.jsonl instead
    return

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=[],  # v2 compatible - no output mapping
    side_effects=['synapse.injection'],
    errors=[]
)
def execute_social_learning_if_needed(ctx: OrchestratorSystemContext):
    """
    Checks logic and executes social learning.
    Note: In Flux V2, the 'if needed' check moves to YAML logic. 
    But simpler to have a safe wrapper that prepares args.
    """
    domain, is_dict = get_domain_ctx(ctx)
    
    active_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    if active_idx >= len(experiments): 
        return

    exp_def = experiments[active_idx]
    exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if not runner: return
    
    log(ctx, "info", f"Executing Social Learning at Episode {runner.current_episode_count}")
        
    if runner.coordinator.agents:
        rankings = runner.coordinator.get_agent_rankings()
        
        pop_contexts = [a.snn_ctx for a in runner.coordinator.agents]
        snn_global = runner.coordinator.agents[0].snn_ctx 
        
        process_social_learning_protocol(
            snn_global,
            pop_contexts,
            rankings
        )
