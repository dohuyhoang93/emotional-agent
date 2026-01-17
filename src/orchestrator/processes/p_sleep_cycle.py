"""
Sleep Cycle Manager
===================
Orchestrates the Biological Sleep phase for all agents.

Author: Theus Agent
Date: 2025-12-31
"""
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr
from src.logger import log

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=[],  # v2 compatible
    side_effects=['agents.sleep'],
    errors=[]
)
def run_sleep_cycle_process(ctx: OrchestratorSystemContext):
    """
    Execute sleep cycle for all agents in the active experiment.
    """
    domain, is_dict = get_domain_ctx(ctx)
    
    active_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return
    
    exp_def = experiments[active_idx]
    exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
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
    for t in range(duration):
        for agent in coordinator.agents:
            if hasattr(agent, 'dream_step'):
                agent.dream_step(t)
                
    # 3. Wake Up
    for agent in coordinator.agents:
        if hasattr(agent, 'wake_up'):
            agent.wake_up()
            
    log(ctx, "info", "🌅 WAKING UP! Sleep cycle complete.")
