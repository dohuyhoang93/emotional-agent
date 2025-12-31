"""
Sleep Cycle Manager
===================
Orchestrates the Biological Sleep phase for all agents.

Author: Theus Agent
Date: 2025-12-31
"""
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=[],
    side_effects=['agents.sleep'],
    errors=[]
)
def run_sleep_cycle_process(ctx: OrchestratorSystemContext):
    """
    Execute sleep cycle for all agents in the active experiment.
    """
    domain = ctx.domain_ctx
    
    # Get active experiment runner
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    if not runner:
        return

    coordinator = runner.coordinator
    # specific config or default
    duration = runner.config.get('sleep_duration', 100)
    
    log(ctx, "info", f"💤 ENTERING SLEEP CYCLE (Duration: {duration} steps)...")
    
    # 1. Enter Sleep Mode
    for agent in coordinator.agents:
        if hasattr(agent, 'start_sleep'):
            agent.start_sleep()
            
    # 2. Dream Loop
    # TODO: In future, this should be an inner workflow loop!
    # For now, keeping the loop inside python for simplicity of legacy 'agent.dream_step'
    for t in range(duration):
        for agent in coordinator.agents:
            if hasattr(agent, 'dream_step'):
                agent.dream_step(t)
                
    # 3. Wake Up
    for agent in coordinator.agents:
        if hasattr(agent, 'wake_up'):
            agent.wake_up()
            
    log(ctx, "info", "🌅 WAKING UP! Sleep cycle complete.")
