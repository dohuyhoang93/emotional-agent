from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log
from src.processes.snn_advanced_features_theus import _revolution_impl

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level'],
    outputs=['domain_ctx', ],
    side_effects=[],
    errors=[]
)
def perform_revolution_protocol(ctx: OrchestratorSystemContext):
    """
    Process: Thực hiện Revolution Protocol (Cultural Evolution).
    """
    domain = ctx.domain_ctx
    bus = domain.event_bus
    
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    # Check if multi-agent coordinator exists
    if not runner or not hasattr(runner, 'coordinator') or not runner.coordinator:
        if bus: bus.emit("REVOLUTION_SKIP")
        return
    
    log(ctx, "info", "✊ Checking Revolution Protocol...")
    
    # Get Population Contexts
    agents = runner.coordinator.agents
    population_contexts = [agent.snn_ctx for agent in agents]
    
    # Execute for each agent
    triggered_count = 0
    for agent in agents:
        # NOTE: RLAgent uses domain_ctx, not ctx
        # Create a minimal SystemContext wrapper for RL
        from src.core.context import SystemContext
        rl_system_ctx = SystemContext(
            global_ctx=None,
            domain_ctx=agent.domain_ctx
        )
        
        _revolution_impl(
            snn_ctx=agent.snn_ctx,
            rl_ctx=rl_system_ctx,
            population_contexts=population_contexts
        )
        
        if agent.snn_ctx.domain_ctx.revolution_triggered:
            triggered_count += 1
            
    if triggered_count > 0:
        log(ctx, "warning", f"🔥 Revolution Triggered by {triggered_count} agents! Ancestors overthrown.")
        if bus: bus.emit("REVOLUTION_DONE")
    else:
        if bus: bus.emit("REVOLUTION_SKIP")

