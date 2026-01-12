"""
Epsilon Decay Process for Orchestrator
========================================
Process decay exploration rate sau mỗi episode (không phải mỗi step).

Author: Do Huy Hoang
Date: 2025-01-12
"""

from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log


@process(
    inputs=[
        'domain_ctx', 'domain', 
        'domain.active_experiment_idx', 'domain.experiments',
        'global_ctx.exploration_decay', 'global_ctx.min_exploration',
        'log_level'  # Required for log() function
    ],
    outputs=['domain', 'domain_ctx'],
    side_effects=[],
    errors=[]
)
def decay_exploration_all_agents(ctx: OrchestratorSystemContext):
    """
    Process: Decay epsilon cho tất cả agents sau mỗi episode.
    
    NOTE: Fix cho bug decay quá nhanh - trước đây decay 100 lần/episode (mỗi step).
    Bây giờ chỉ decay 1 lần sau mỗi episode hoàn thành.
    
    Logic: epsilon = max(min_epsilon, epsilon * decay_rate)
    """
    domain = ctx.domain_ctx
    
    # Get current experiment runner
    if domain.active_experiment_idx >= len(domain.experiments):
        return
        
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    if not runner or not hasattr(runner, 'coordinator'):
        return
    
    coordinator = runner.coordinator
    
    # Get config từ Experiment Global Context (NOT Orchestrator Global Context)
    decay_rate = getattr(coordinator.global_ctx, 'exploration_decay', 0.995)
    min_epsilon = getattr(coordinator.global_ctx, 'min_exploration', 0.05)
    
    # Decay epsilon cho tất cả agents
    for agent in coordinator.agents:
        current_eps = agent.rl_ctx.domain_ctx.current_exploration_rate
        new_eps = max(min_epsilon, current_eps * decay_rate)
        agent.rl_ctx.domain_ctx.current_exploration_rate = new_eps
    
    # Log decay (debug)
    if coordinator.agents:
        sample_eps = coordinator.agents[0].rl_ctx.domain_ctx.current_exploration_rate
        log(ctx, "debug", f"Epsilon decayed to {sample_eps:.4f}")
