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
def run_population_dreaming(ctx: OrchestratorSystemContext):
    """
    Process: Chạy quy trình Dreaming cho toàn bộ Population.
    """
    domain, is_dict = get_domain_ctx(ctx)
    bus = get_attr(domain, 'event_bus', None)
    
    active_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {}
    
    exp_def = experiments[active_idx]
    exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if runner:
        log(ctx, "info", "💤 Population is SLEEPING (Dreaming & Consolidation)...")
        
        # Use the Engine that RLAgent holds
        for agent in runner.coordinator.agents:
            if hasattr(agent, 'engine'):
                agent.engine.execute_workflow("workflows/agent_dream.yaml")
        
    if bus: bus.emit("DREAM_DONE")
