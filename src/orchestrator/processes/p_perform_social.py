from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus'],
    outputs=[],
    side_effects=[],
    errors=[]
)
def perform_social_transfer(ctx: OrchestratorSystemContext):
    """
    Process: Thực hiện Social Learning (Orchestrator Level).
    """
    domain = ctx.domain_ctx
    bus = domain.event_bus
    
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    if runner and runner.social_learning:
        log(ctx, "info", "🧠 Performing Social Learning Transfer...")
        runner.social_learning.perform_social_learning()
        stats = runner.social_learning.get_transfer_stats()
        runner.logger.log_social_learning(stats)
    
    if bus: bus.emit("SOCIAL_DONE")
