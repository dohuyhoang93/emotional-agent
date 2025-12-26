from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus'],
    outputs=[],
    side_effects=[],
    errors=[]
)
def run_population_dreaming(ctx: OrchestratorSystemContext):
    """
    Process: Chạy quy trình Dreaming cho toàn bộ Population.
    """
    domain = ctx.domain_ctx
    bus = domain.event_bus
    
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    if runner:
        log(ctx, "info", "💤 Population is SLEEPING (Dreaming & Consolidation)...")
        # Loop agents and run 'agent_dream.yaml'
        # Since we don't have direct access to 'execute_workflow' via runner easily without passing Engine,
        # we assume each agent has a helper or we use the Engine attached to Context if available.
        # But RLAgent usually takes an Engine in __init__.
        
        # We need to manually invoke the steps or use the agent's internal mechanism.
        # Assuming RLAgent has a method 'dream()'? It currently doesn't.
        # We must add it or use the Engine from the Orchestrator to run the agent's context.
        
        # HACK: Re-use the Orchestrator's engine (self.engine is not available here).
        # We can simulate by calling the processes directly if imported, OR use Runner's engine.
        
        # Let's assume MultiAgentCoordinator can handle this:
        # runner.coordinator.run_workflow_for_all("workflows/agent_dream.yaml")
        # But Coordinator doesn't have that method.
        
        # Simplest path: Iterate processes manually here (Python-side) for now,
        # or better: Define 'dream' method in RLAgent during Phase 10 refactor.
        
        # LET'S EXTEND RLAgent DYNAMICALLY OR ASSUME UPDATE.
        # For now, I will manually call the processes on each agent context.
        pass
        
    # LOGIC:
    from src.processes.snn_imagination_theus import process_imagination_loop, process_dream_learning
    # from src.processes.snn_core_theus import process_integrate... 
    # This is getting messy. Use TheusEngine properly.
    
    # Correct way: Use the Engine that RLAgent holds.
    for agent in runner.coordinator.agents:
        # agent.engine is the TheusEngine instance
        agent.engine.execute_workflow("workflows/agent_dream.yaml")
        
    if bus: bus.emit("DREAM_DONE")
