import json
import os
from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log, log_error

@process(
    inputs=['domain.experiments', 'log_level', 'domain.output_dir'],
    outputs=['domain.experiments'],
    side_effects=['filesystem.read'],
    errors=['json.JSONDecodeError']
)
def aggregate_results(ctx: OrchestratorSystemContext):
    """
    Process: Aggregate results from multi-agent experiment runs.
    
    NOTE: Updated to handle JSON metrics from MultiAgentExperiment.
    """
    log(ctx, "info", "  [Orchestration] Aggregating results...")
    domain = ctx.domain_ctx

    for exp_def in domain.experiments:
        log(ctx, "info", f"    [Experiment: {exp_def.name}] Aggregating data...")
        
        all_runs_metrics = []
        if not exp_def.list_of_runs:
            # Fallback for FSM Architecture (Single Run / Implicit)
            checkpoints_dir = os.path.join(domain.output_dir, f"{exp_def.name}_checkpoints")
            metrics_path = os.path.join(checkpoints_dir, "metrics.json")
            
            if os.path.exists(metrics_path):
                try:
                    with open(metrics_path, 'r') as f:
                        run_data = json.load(f)
                    
                    # FSM Format: List of {'episode': int, 'metrics': dict}
                    if isinstance(run_data, list):
                        # Flatten metrics for plotter
                        for entry in run_data:
                            flat_metrics = entry.get('metrics', {}).copy()
                            flat_metrics['episode'] = entry.get('episode')
                            flat_metrics['run_id'] = 0 # Single run assumption
                            all_runs_metrics.append(flat_metrics)
                    # Legacy Format fallback
                    elif isinstance(run_data, dict):
                        metrics = run_data.get('metrics', [])
                        all_runs_metrics.extend(metrics)
                        
                    log(ctx, "info", f"    [Experiment: {exp_def.name}] Loaded FSM metrics from {metrics_path}.")
                except Exception as e:
                    log_error(ctx, f"Cannot read FSM metrics file '{metrics_path}': {e}")
            else:
                log(ctx, "info", f"    [Experiment: {exp_def.name}] No legacy runs and no FSM metrics found.")

        # Legacy Run Logic
        for exp_run in exp_def.list_of_runs:
            if exp_run.status == "COMPLETED" and exp_run.output_csv_path and os.path.exists(exp_run.output_csv_path):
                try:
                    # Load JSON metrics
                    with open(exp_run.output_csv_path, 'r') as f:
                        run_data = json.load(f)
                    
                    # Extract metrics history
                    metrics = run_data.get('metrics', [])
                    
                    # Add run_id to each episode
                    for episode_metrics in metrics:
                        episode_metrics['run_id'] = exp_run.run_id
                    
                    all_runs_metrics.extend(metrics)
                    
                except Exception as e:
                    log_error(ctx, f"Cannot read metrics file '{exp_run.output_csv_path}': {e}")
            elif exp_run.status == "FAILED":
                log(ctx, "info", f"WARNING: Run {exp_run.run_id} of experiment '{exp_def.name}' failed, skipping.")
            else:
                log(ctx, "info", f"WARNING: Metrics file '{exp_run.output_csv_path}' does not exist or run not completed, skipping.")
        
        if all_runs_metrics:
            # Store as list of dicts (easier to work with than DataFrame for JSON data)
            exp_def.aggregated_data = all_runs_metrics
            log(ctx, "info", f"    [Experiment: {exp_def.name}] Aggregated data for {len(exp_def.list_of_runs)} runs, {len(all_runs_metrics)} episodes total.")
        else:
            log(ctx, "info", f"    [Experiment: {exp_def.name}] No data to aggregate.")
            exp_def.aggregated_data = []

    log(ctx, "info", "  [Orchestration] Aggregation complete.")
