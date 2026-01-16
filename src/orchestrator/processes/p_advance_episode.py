from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.active_experiment_episode_idx'],
    outputs=['domain', 'domain_ctx', 'domain.active_experiment_episode_idx'],
    side_effects=[],
    errors=[]
)
def advance_episode_index(ctx: OrchestratorSystemContext):
    """
    Increments the active experiment's episode index.
    """
    domain = ctx.domain_ctx
    
    # Process Logic
    current_idx = domain.active_experiment_episode_idx
    new_idx = current_idx + 1
    print(f"DEBUG: Advance Episode {current_idx} -> {new_idx}")
    
    # Sync back to runner (optional, for compatibility)
    # Required for Checks like 'episodes_per_run' which accesses runner.
    exp_def = domain.experiments[domain.active_experiment_idx]
    
    # V3 MIGRATION: Fetch from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_def.name)
    
    if runner:
        runner.current_episode_count = new_idx
        
        # Sync to SNN Global Context for Revolution cooldown
        if hasattr(runner, 'coordinator') and runner.coordinator:
            for agent in runner.coordinator.agents:
                agent.snn_ctx.global_ctx.current_episode = new_idx
                
    # V3 WORKAROUND: In-Place Mutation because Framework Patch is unstable/unverified
    # We update `active_experiment_episode_idx` in-place
    # Theus V3 engine update logic via keys proved problematic (reverts state).
    domain.active_experiment_episode_idx = new_idx
    
    # Return empty to avoid Engine update logic
    return {}
