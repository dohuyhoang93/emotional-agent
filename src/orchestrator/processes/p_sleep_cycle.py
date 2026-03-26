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
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=['domain.sig_sleep_step', 'domain.sig_sleep_duration'],
    side_effects=['agents.sleep'],
    errors=[]
)
def prepare_sleep_cycle(ctx: OrchestratorSystemContext):
    """
    1. Initialize sleep signals.
    2. Call start_sleep() on all agents.
    """
    domain = ctx.domain
    active_idx = getattr(domain, 'active_experiment_idx', 0)
    experiments = getattr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {'domain.sig_sleep_step': 0, 'domain.sig_sleep_duration': 0}
    
    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown') if not isinstance(exp_def, dict) else exp_def.get('name', 'unknown')
    
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    if not runner:
        return {'domain.sig_sleep_step': 0, 'domain.sig_sleep_duration': 0}

    coordinator = runner.coordinator
    duration = runner.config.get('sleep_duration', 100)
    
    log(ctx, "info", f"💤 PREPARING SLEEP CYCLE (Duration: {duration} steps)...")
    
    for agent in coordinator.agents:
        if hasattr(agent, 'start_sleep'):
            agent.start_sleep()
            
    return {
        'domain.sig_sleep_step': 0,
        'domain.sig_sleep_duration': duration
    }

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.sig_sleep_step'],
    outputs=[],
    side_effects=['agents.dream'],
    errors=[]
)
def execute_dream_step(ctx: OrchestratorSystemContext):
    """
    Execute a single dream step for all agents.
    """
    domain = ctx.domain
    active_idx = getattr(domain, 'active_experiment_idx', 0)
    experiments = getattr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {}
        
    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown') if not isinstance(exp_def, dict) else exp_def.get('name', 'unknown')
    
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    if not runner or not runner.coordinator:
        return {}

    t = getattr(domain, 'sig_sleep_step', 0)
    for agent in runner.coordinator.agents:
        if hasattr(agent, 'dream_step'):
            agent.dream_step(t)
    
    return {}

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments'],
    outputs=['domain.sig_sleep_step', 'domain.sig_sleep_duration'],
    side_effects=['agents.wake'],
    errors=[]
)
def finalize_sleep_cycle(ctx: OrchestratorSystemContext):
    """
    1. Call wake_up() on all agents.
    2. Reset sleep signals.
    """
    domain = ctx.domain
    active_idx = getattr(domain, 'active_experiment_idx', 0)
    experiments = getattr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {'domain.sig_sleep_step': 0, 'domain.sig_sleep_duration': 0}
        
    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown') if not isinstance(exp_def, dict) else exp_def.get('name', 'unknown')
    
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    if not runner or not runner.coordinator:
        return {'domain.sig_sleep_step': 0, 'domain.sig_sleep_duration': 0}

    for agent in runner.coordinator.agents:
        if hasattr(agent, 'wake_up'):
            agent.wake_up()
            
    log(ctx, "info", "🌅 WAKING UP! Sleep cycle complete.")
    
    return {
        'domain.sig_sleep_step': 0,
        'domain.sig_sleep_duration': 0
    }

@process(
    inputs=['domain.sig_sleep_step'],
    outputs=['domain.sig_sleep_step'],
    side_effects=[],
    errors=[]
)
def advance_sleep_step(ctx: OrchestratorSystemContext):
    """Increment the sleep step counter."""
    domain = ctx.domain
    current = getattr(domain, 'sig_sleep_step', 0)
    return {'domain.sig_sleep_step': current + 1}
