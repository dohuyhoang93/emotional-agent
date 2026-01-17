from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr
from src.logger import log

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level'],
    outputs=[],  # v2 compatible
    side_effects=[],
    errors=[]
)
def perform_social_transfer(ctx: OrchestratorSystemContext):
    """
    Process: Thực hiện Social Learning (Orchestrator Level).
    """
    domain, is_dict = get_domain_ctx(ctx)
    bus = get_attr(domain, 'event_bus', None)
    
    active_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return
    
    exp_def = experiments[active_idx]
    exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if runner and runner.social_learning:
        log(ctx, "info", "🧠 Performing Social Learning Transfer...")
        runner.social_learning.perform_social_learning()
        stats = runner.social_learning.get_transfer_stats()
        runner.logger.log_social_learning(stats)
    
    if bus: bus.emit("SOCIAL_DONE")
