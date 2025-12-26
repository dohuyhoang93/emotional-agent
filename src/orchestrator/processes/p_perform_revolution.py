from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log
from src.processes.snn_advanced_features_theus import process_revolution_protocol

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus'],
    outputs=[],
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
    
    if runner and runner.revolution:
        log(ctx, "info", "✊ Checking Revolution Protocol...")
        
        # Get Population Contexts
        agents = runner.coordinator.agents
        population_contexts = [agent.snn_ctx for agent in agents]
        
        # Execute for each agent
        triggered_count = 0
        for agent in agents:
            # Manually invoke the advanced process logic
            # This logic needs access to both SNN and RL contexts.
            # Agent has agent.snn_ctx and agent.ctx (RL)
            
            process_revolution_protocol(
                snn_ctx=agent.snn_ctx,
                rl_ctx=agent.ctx,
                population_contexts=population_contexts
            )
            
            if agent.snn_ctx.domain_ctx.revolution_triggered:
                triggered_count += 1
                
        if triggered_count > 0:
            log(ctx, "warning", f"🔥 Revolution Triggered by {triggered_count} agents! Ancestors overthrown.")
            if bus: bus.emit("REVOLUTION_DONE")
        else:
            if bus: bus.emit("REVOLUTION_SKIP")
            
    else:
        if bus: bus.emit("REVOLUTION_SKIP")
