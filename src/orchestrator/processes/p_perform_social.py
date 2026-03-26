from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level'],
    outputs=[],
    side_effects=[],
    errors=[]
)
def perform_social_transfer(ctx: OrchestratorSystemContext):
    """
    Process: Thực hiện Social Learning (Orchestrator Level).
    """
    bus = getattr(ctx.domain, 'event_bus', None)
    
    active_idx = getattr(ctx.domain, 'active_experiment_idx', 0)
    experiments = getattr(ctx.domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {}
    
    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown')
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if runner and runner.social_learning:
        log(ctx, "info", "🧠 Performing Social Learning Transfer...")
        runner.social_learning.perform_social_learning()
        stats = runner.social_learning.get_transfer_stats()
        runner.logger.log_social_learning(stats)
    
    if bus: bus.emit("SOCIAL_DONE")
