from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log
import os
import json
from src.processes.snn_social_learning_theus import process_social_learning_protocol

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=['domain', 'domain_ctx', 'domain.active_experiment_idx'],
    side_effects=[],
    errors=[]
)
def advance_experiment_index(ctx: OrchestratorSystemContext):
    """
    Increments the active experiment index.
    """
    ctx.domain_ctx.active_experiment_idx += 1
    log(ctx, "info", f"⏩ Advanced to Experiment Index: {ctx.domain_ctx.active_experiment_idx}")

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.output_dir', 'domain.metrics', 'domain.active_experiment_episode_idx'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def save_metrics_snapshot(ctx: OrchestratorSystemContext):
    """
    DEPRECATED: Saves current metrics to JSON checkpoint.
    
    NOTE: This process is now disabled. Metrics are logged via JSONL only (p_log_metrics.py).
    The legacy metrics.json format is no longer maintained.
    """
    # Legacy JSON snapshot disabled - use metrics.jsonl instead
    return

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=['domain', 'domain_ctx', 'domain.metrics'],
    side_effects=['synapse.injection'],
    errors=[]
)
def execute_social_learning_if_needed(ctx: OrchestratorSystemContext):
    """
    Checks logic and executes social learning.
    Note: In Flux V2, the 'if needed' check moves to YAML logic. 
    But simpler to have a safe wrapper that prepares args.
    """
    domain = ctx.domain_ctx
    if domain.active_experiment_idx >= len(domain.experiments): return

    exp_def = domain.experiments[domain.active_experiment_idx]
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_def.name)
    
    if not runner: return
    
    log(ctx, "info", f"Executing Social Learning at Episode {runner.current_episode_count}")
        
    if runner.coordinator.agents:
        rankings = runner.coordinator.get_agent_rankings()
        # Use Agent 0's SNN Context as the "Global" SNN Context (contains system-wide params)
        # Note: We need a dedicated SNNSystemContext wrapper if process_social_learning expects one.
        # But process_social_learning expects (global_snn_ctx, pop_contexts, rankings)
        # It accesses global_snn_ctx.global_ctx -> SNNGlobalContext.
        
        # In FSMRunner we created snn_global_ctx, but we didn't store it in Orchestrator Context explicitly?
        # Coordinator has it.
        # runner.coordinator.global_snn_context is what we passed in init?
        # MultiAgentCoordinator stores it in self.global_snn_context?
        # Let's check Coordinator.
        # Assuming Agent 0 has a pointer or copy.
        
        # Create a mock wrapper or reuse existing structure.
        # Ideally, we should have stored snn_global_ctx in FSMRunner.
        
        # Workaround based on p_run_simulations: 
        # "snn_global = runner.coordinator.agents[0].snn_ctx"
        # This implies Agent 0's context holds the config.
        
        pop_contexts = [a.snn_ctx for a in runner.coordinator.agents]
        snn_global = runner.coordinator.agents[0].snn_ctx 
        
        process_social_learning_protocol(
            snn_global,
            pop_contexts,
            rankings
        )
