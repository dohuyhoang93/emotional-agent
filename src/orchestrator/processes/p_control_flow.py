from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log
import os
import json
from src.processes.snn_social_learning_theus import process_social_learning_protocol

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=['domain.active_experiment_idx'],
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
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.output_dir', 'domain.metrics', 'domain.active_experiment_episode_idx'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def save_metrics_snapshot(ctx: OrchestratorSystemContext):
    """
    Saves current metrics to JSON checkpoint.
    Replaces inline logic from p_run_simulations.
    """
    domain = ctx.domain_ctx
    if domain.active_experiment_idx >= len(domain.experiments):
        return

    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    if not runner: return

    # Check if we have metrics to save
    if not hasattr(domain, 'metrics') or not domain.metrics:
        return

    # Determine file path
    output_dir = domain.output_dir or "results"
    exp_name = exp_def.name
    checkpoint_dir = os.path.join(output_dir, f"{exp_name}_checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)
    metrics_file = os.path.join(checkpoint_dir, "metrics.json")
    
    # Load existing
    existing_data = []
    if os.path.exists(metrics_file):
        try:
            with open(metrics_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except json.JSONDecodeError:
            existing_data = []
    
    # Convert metrics to plain dict recursively to handle FrozenDict/FrozenList
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif hasattr(obj, 'items'): # Duck typing for FrozenDict
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [sanitize(v) for v in obj]
        elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
             return [sanitize(v) for v in obj]
        return obj
    
    clean_metrics = sanitize(domain.metrics)

    # Determine Episode Number (POP Style)
    # active_experiment_episode_idx points to NEXT episode
    current_ep_idx = domain.active_experiment_episode_idx - 1
    
    # Check for duplicates
    existing_eps = [entry.get('episode') for entry in existing_data]
    if current_ep_idx in existing_eps:
        # log(ctx, "debug", f"Metrics for Ep {current_ep_idx} already saved. Skipping.")
        return

    # Append
    existing_data.append({
        "episode": current_ep_idx,
        "metrics": clean_metrics
    })
    
    # Write back
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, indent=2)
    
    # log(ctx, "debug", f"Saved metrics snapshot for Ep {runner.current_episode_count}")

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'log_level'],
    outputs=['domain.metrics'],
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
    runner = getattr(exp_def, 'runner', None)
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
