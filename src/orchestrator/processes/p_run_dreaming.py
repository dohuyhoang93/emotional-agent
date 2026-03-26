from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level'],
    outputs=[],
    side_effects=[],
    errors=[]
)
def run_population_dreaming(ctx: OrchestratorSystemContext):
    """
    Process: Chạy quy trình Dreaming cho toàn bộ Population.
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
    
    if runner:
        log(ctx, "info", "💤 Population is SLEEPING (Dreaming & Consolidation)...")
        
        # Use the Engine that RLAgent holds
        for agent in runner.coordinator.agents:
            if hasattr(agent, 'engine'):
                agent.engine.execute_workflow("workflows/agent_dream.yaml")
        
    if bus: bus.emit("DREAM_DONE")
