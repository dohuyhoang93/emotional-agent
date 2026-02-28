from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr, set_attr

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.active_experiment_episode_idx'],
    outputs=[],  
    side_effects=[],
    errors=[]
)
def advance_episode_index(ctx: OrchestratorSystemContext):
    """
    Increments the active experiment's episode index.
    Returns values for implicit mapping (SIGNAL-BASED).
    """
    domain, is_dict = get_domain_ctx(ctx)
    
    # Get current signal values
    current_sig_counter = get_attr(domain, 'sig_episode_counter', 0)
    
    # Legacy Sync
    current_idx_legacy = get_attr(domain, 'active_experiment_episode_idx', 0)
    
    # Get experiment info
    active_exp_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    new_sig_counter = current_sig_counter + 1
    new_idx_legacy = current_idx_legacy + 1
    
    # Get experiment name
    if active_exp_idx < len(experiments):
        exp_def = experiments[active_exp_idx]
        exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
        
        # V3 MIGRATION: Fetch from Registry
        from src.orchestrator.runtime_registry import get_runner
        runner = get_runner(exp_name)
        
        if runner:
            runner.current_episode_count = new_sig_counter
            
            # Sync to SNN Global Context for Revolution cooldown
            if hasattr(runner, 'coordinator') and runner.coordinator:
                for agent in runner.coordinator.agents:
                    agent.snn_ctx.global_ctx.current_episode = new_sig_counter
    
    # 1. Update Python Domain Object (In-Place)
    set_attr(domain, 'sig_episode_counter', new_sig_counter)
    set_attr(domain, 'active_experiment_episode_idx', new_idx_legacy) # Keep legacy sync
    
    # Return nothing
    return {}
