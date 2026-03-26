import json
import os
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log, log_error

@process(
    inputs=['domain_ctx', 'domain', 'domain.experiments', 'log_level', 'domain.output_dir'],
    outputs=['domain'],
    side_effects=['filesystem.read', 'filesystem.write'],
    errors=['json.JSONDecodeError']
)
def aggregate_results(ctx: OrchestratorSystemContext):
    """
    Process: Aggregate results from multi-agent experiment runs.
    
    NOTE: Updated to handle JSON metrics from MultiAgentExperiment.
    """
    log(ctx, "info", "  [Orchestration] Aggregating results...")
    
    experiments = getattr(ctx.domain, 'experiments', [])
    output_dir = getattr(ctx.domain, 'output_dir', 'results')

    for exp_def in experiments:
        exp_name = getattr(exp_def, 'name', 'unknown')
        log(ctx, "info", f"    [Experiment: {exp_name}] Aggregating data...")
        
        list_of_runs = getattr(exp_def, 'list_of_runs', [])
        
        all_runs_metrics = []
        if not list_of_runs:
            # NOTE: FSM Architecture uses {exp_name}/ directly,
            # Legacy uses {exp_name}_checkpoints/. Try both.
            checkpoints_dir = os.path.join(output_dir, exp_name)
            metrics_path = os.path.join(checkpoints_dir, "metrics.jsonl")
            
            if not os.path.exists(metrics_path):
                 metrics_path = os.path.join(checkpoints_dir, "metrics.json")
            
            if not os.path.exists(metrics_path):
                 checkpoints_dir = os.path.join(output_dir, f"{exp_name}_checkpoints")
                 metrics_path = os.path.join(checkpoints_dir, "metrics.jsonl")
            
            if not os.path.exists(metrics_path):
                 metrics_path = os.path.join(checkpoints_dir, "metrics.json")
            
            if os.path.exists(metrics_path):
                try:
                    all_runs_metrics = []
                    
                    if metrics_path.endswith('.jsonl'):
                        with open(metrics_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                if line.strip():
                                    entry = json.loads(line)
                                    flat_metrics = entry.get('metrics', {}).copy()
                                    flat_metrics['episode'] = entry.get('episode')
                                    flat_metrics['timestamp'] = entry.get('timestamp')
                                    flat_metrics['run_id'] = 0
                                    all_runs_metrics.append(flat_metrics)
                        
                        log(ctx, "info", f"    [Experiment: {exp_name}] Loaded {len(all_runs_metrics)} episodes from {metrics_path} (JSONL).")

                    else:
                        with open(metrics_path, 'r') as f:
                            run_data = json.load(f)
                        
                        if isinstance(run_data, list):
                            for entry in run_data:
                                flat_metrics = entry.get('metrics', {}).copy()
                                flat_metrics['episode'] = entry.get('episode')
                                flat_metrics['run_id'] = 0
                                all_runs_metrics.append(flat_metrics)
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
            run_status = getattr(exp_run, 'status', 'PENDING')
            output_csv_path = getattr(exp_run, 'output_csv_path', '')
            run_id = getattr(exp_run, 'run_id', 0)
            
            if run_status == "COMPLETED" and output_csv_path and os.path.exists(output_csv_path):
                try:
                    with open(output_csv_path, 'r') as f:
                        run_data = json.load(f)
                    
                    metrics = run_data.get('metrics', [])
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
            # NOTE: Duck-typing — works for both dict and object exp_def
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
    return {
        'domain.experiments': experiments
    }
