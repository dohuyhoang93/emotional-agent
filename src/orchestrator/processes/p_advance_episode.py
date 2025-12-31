from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.active_experiment_episode_idx'],
    outputs=['domain.active_experiment_episode_idx'],
    side_effects=[],
    errors=[]
)
def advance_episode_index(ctx: OrchestratorSystemContext):
    """
    Process: Increment the episode index for the active experiment.
    Keeps state management separate from execution logic.
    """
    domain = ctx.domain_ctx
    
    # Update State (POP Style)
    domain.active_experiment_episode_idx += 1
    
    # Sync back to runner (optional, for compatibility)
    # Required for Checks like 'episodes_per_run' which accesses runner.
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    if runner:
        runner.current_episode_count = domain.active_experiment_episode_idx
