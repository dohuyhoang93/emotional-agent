from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.active_experiment_episode_idx'],
    outputs=['domain.sig_episode_counter', 'domain.active_experiment_episode_idx'],
    side_effects=[],
    errors=[]
)
def advance_episode_index(ctx: OrchestratorSystemContext):
    """
    Increments the active experiment's episode index.
    Returns values for implicit mapping (SIGNAL-BASED).
    """
    # Get current signal values
    current_sig_counter = getattr(ctx.domain, 'sig_episode_counter', 0)
    current_idx_legacy = getattr(ctx.domain, 'active_experiment_episode_idx', 0)
    
    # Get experiment info
    active_exp_idx = getattr(ctx.domain, 'active_experiment_idx', 0)
    experiments = getattr(ctx.domain, 'experiments', [])
    
    new_sig_counter = current_sig_counter + 1
    new_idx_legacy = current_idx_legacy + 1
    
    # Get experiment name
    if active_exp_idx < len(experiments):
        exp_def = experiments[active_exp_idx]
        exp_name = getattr(exp_def, 'name', 'unknown')
        
        # V3 MIGRATION: Fetch from Registry
        from src.orchestrator.runtime_registry import get_runner
        runner = get_runner(exp_name)
        
        if runner:
            runner.current_episode_count = new_sig_counter
            
            # Sync to SNN Global Context for Revolution cooldown
            if hasattr(runner, 'coordinator') and runner.coordinator:
                for agent in runner.coordinator.agents:
                    agent.snn_ctx.global_ctx.current_episode = new_sig_counter
    
    # PHYSICS OVERRIDE: Cấp quyền update cho các biến signal trong Theus 3.0.36
    try:
        import theus_core
        theus_core.register_physics_override("domain.sig_episode_counter", 31)
    except Exception:
        pass

    # Return StateUpdate Delta
    return {
        'domain.sig_episode_counter': new_sig_counter,
        'domain.active_experiment_episode_idx': new_idx_legacy
    }
