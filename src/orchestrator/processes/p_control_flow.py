from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log
import os
import json
from src.processes.snn_social_learning_theus import process_social_learning_protocol

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=['domain.sig_experiment_active_idx', 'domain.active_experiment_idx'],
    side_effects=[],
    errors=[]
)
def advance_experiment_index(ctx: OrchestratorSystemContext):
    """
    Increments the active experiment index.
    Returns values for implicit mapping (SIGNAL-BASED).
    """
    current_sig_idx = getattr(ctx.domain, 'sig_experiment_active_idx', 0)
    current_idx_legacy = getattr(ctx.domain, 'active_experiment_idx', 0)
    
    new_sig_idx = current_sig_idx + 1
    new_idx_legacy = current_idx_legacy + 1
    
    # PHYSICS OVERRIDE: Allow UPDATE (4) + READ (1) = 5, or full caps (31) 
    # to bypass the Signal Zone Physics (Flow only - no update).
    try:
        import theus_core
        theus_core.register_physics_override("domain.sig_experiment_active_idx", 31)
    except Exception:
        pass
    
    log(ctx, "info", f"⏩ Advanced to Experiment Index: {new_sig_idx}")
    
    # Return StateUpdate Delta to Engine
    return {
        'domain.sig_experiment_active_idx': new_sig_idx,
        'domain.active_experiment_idx': new_idx_legacy
    }

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.output_dir', 'domain.metrics', 'domain.active_experiment_episode_idx'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def save_metrics_snapshot(ctx: OrchestratorSystemContext):
    """
    DEPRECATED: Saves current metrics to JSON checkpoint.
    """
    return {}

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=[],
    side_effects=['synapse.injection'],
    errors=[]
)
def execute_social_learning_if_needed(ctx: OrchestratorSystemContext):
    """
    Checks logic and executes social learning.
    """
    active_idx = getattr(ctx.domain, 'active_experiment_idx', 0)
    experiments = getattr(ctx.domain, 'experiments', [])
    
    if active_idx >= len(experiments): 
        return {}

    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown')
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if not runner: return {}
    
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
    return {}
