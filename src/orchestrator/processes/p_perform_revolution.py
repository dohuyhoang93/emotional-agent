from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr
from src.logger import log
from src.processes.snn_advanced_features_theus import _revolution_impl

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level'],
    outputs=[],  # v2 compatible
    side_effects=[],
    errors=[]
)
def perform_revolution_protocol(ctx: OrchestratorSystemContext):
    """
    Process: Thực hiện Revolution Protocol (Cultural Evolution).
    """
    domain, is_dict = get_domain_ctx(ctx)
    bus = get_attr(domain, 'event_bus', None)
    
    active_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        if bus: bus.emit("REVOLUTION_SKIP")
        return {}
    
    exp_def = experiments[active_idx]
    exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    # Check if multi-agent coordinator exists
    if not runner or not hasattr(runner, 'coordinator') or not runner.coordinator:
        if bus: bus.emit("REVOLUTION_SKIP")
        return {}
    
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
