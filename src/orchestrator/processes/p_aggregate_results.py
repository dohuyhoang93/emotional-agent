import json
import os
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr
from src.logger import log, log_error

@process(
    inputs=['domain_ctx', 'domain', 'domain.experiments', 'log_level', 'domain.output_dir'],
    outputs=['domain'],  # Fixed ContractViolationError
    side_effects=['filesystem.read', 'filesystem.write'],
    errors=['json.JSONDecodeError']
)
def aggregate_results(ctx: OrchestratorSystemContext):
    """
    Process: Aggregate results from multi-agent experiment runs.
    
    NOTE: Updated to handle JSON metrics from MultiAgentExperiment.
    """
    log(ctx, "info", "  [Orchestration] Aggregating results...")
    domain, is_dict = get_domain_ctx(ctx)
    
    experiments = get_attr(domain, 'experiments', [])
    output_dir = get_attr(domain, 'output_dir', 'results')

    for exp_def in experiments:
        exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
        log(ctx, "info", f"    [Experiment: {exp_name}] Aggregating data...")
        
        list_of_runs = get_attr(exp_def, 'list_of_runs', []) if isinstance(exp_def, dict) else exp_def.list_of_runs
        
        all_runs_metrics = []
        if not list_of_runs:
            # Fallback for FSM Architecture (Single Run / Implicit)
            checkpoints_dir = os.path.join(output_dir, f"{exp_name}_checkpoints")
            metrics_path = os.path.join(checkpoints_dir, "metrics.jsonl")
            
            if not os.path.exists(metrics_path):
                 # Try legacy json
                 metrics_path = os.path.join(checkpoints_dir, "metrics.json")
            
            if os.path.exists(metrics_path):
                try:
                    all_runs_metrics = []
                    
                    if metrics_path.endswith('.jsonl'):
                        with open(metrics_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip():
                                    entry = json.loads(line)
                                    # Flatten: Merge 'metrics' into top level
                                    flat_metrics = entry.get('metrics', {}).copy()
                                    flat_metrics['episode'] = entry.get('episode')
                                    flat_metrics['timestamp'] = entry.get('timestamp')
                                    flat_metrics['run_id'] = 0
                                    all_runs_metrics.append(flat_metrics)
                        
                        log(ctx, "info", f"    [Experiment: {exp_name}] Loaded {len(all_runs_metrics)} episodes from {metrics_path} (JSONL).")

                    else:
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
                            
                        log(ctx, "info", f"    [Experiment: {exp_name}] Loaded FSM metrics from {metrics_path}.")
                except Exception as e:
                    log_error(ctx, f"Cannot read FSM metrics file '{metrics_path}': {e}")
            else:
                log(ctx, "info", f"    [Experiment: {exp_name}] No legacy runs and no FSM metrics found.")

        # Legacy Run Logic
        for exp_run in list_of_runs:
            run_status = get_attr(exp_run, 'status', 'PENDING') if isinstance(exp_run, dict) else exp_run.status
            output_csv_path = get_attr(exp_run, 'output_csv_path', '') if isinstance(exp_run, dict) else exp_run.output_csv_path
            run_id = get_attr(exp_run, 'run_id', 0) if isinstance(exp_run, dict) else exp_run.run_id
            
            if run_status == "COMPLETED" and output_csv_path and os.path.exists(output_csv_path):
                try:
                    # Load JSON metrics
                    with open(output_csv_path, 'r') as f:
                        run_data = json.load(f)
                    
                    # Extract metrics history
                    metrics = run_data.get('metrics', [])
                    
                    # Add run_id to each episode
                    for episode_metrics in metrics:
                        episode_metrics['run_id'] = run_id
                    
                    all_runs_metrics.extend(metrics)
                    
                except Exception as e:
                    log_error(ctx, f"Cannot read metrics file '{output_csv_path}': {e}")
            elif run_status == "FAILED":
                log(ctx, "info", f"WARNING: Run {run_id} of experiment '{exp_name}' failed, skipping.")
            else:
                log(ctx, "info", f"WARNING: Metrics file '{output_csv_path}' does not exist or run not completed, skipping.")
        
        if all_runs_metrics:
            # Store as list of dicts
            if isinstance(exp_def, dict):
                exp_def['aggregated_data'] = all_runs_metrics
            else:
                exp_def.aggregated_data = all_runs_metrics
            log(ctx, "info", f"    [Experiment: {exp_name}] Aggregated data for {len(list_of_runs)} runs, {len(all_runs_metrics)} episodes total.")
            
            # === LEGACY SUPPORT: RAW CSV DUMP ===
            try:
                import pandas as pd
                df = pd.DataFrame(all_runs_metrics)
                csv_filename = f"{exp_name}_aggregated.csv"
                csv_path = os.path.join(output_dir, csv_filename)
                df.to_csv(csv_path, index=False)
                log(ctx, "info", f"    [Legacy] Dumped raw data to {csv_path}")
            except ImportError:
                 log(ctx, "info", "    [Legacy] Pandas not installed, skipping CSV dump.")
            except Exception as e:
                 log_error(ctx, f"    [Legacy] Failed to dump CSV: {e}")
            # ====================================
            
        else:
            log(ctx, "info", f"    [Experiment: {exp_name}] No data to aggregate.")
            if isinstance(exp_def, dict):
                exp_def['aggregated_data'] = []
            else:
                exp_def.aggregated_data = []

    log(ctx, "info", "  [Orchestration] Aggregation complete.")
    return {}
