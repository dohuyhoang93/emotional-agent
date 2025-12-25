import os
import json
import random
import concurrent.futures
from typing import Dict, Any

from theus import process
from src.orchestrator.context import OrchestratorSystemContext, ExperimentRun
from src.logger import log, log_error

# Import MultiAgentExperiment
import sys
sys.path.append('.')
from experiments.run_multi_agent_experiment import MultiAgentExperiment

def _execute_single_run(
    run_id: int,
    exp_name: str,
    parameters: Dict[str, Any],
    log_level: str,
    episodes: int,
    output_dir: str
) -> dict:
    """
    Execute a single multi-agent experiment run.
    
    NOTE: Updated to use MultiAgentExperiment directly instead of subprocess.
    """
    seed = random.randint(0, 1000000)
    
    # Prepare config for MultiAgentExperiment
    config = {
        'name': f"{exp_name}_run_{run_id}",
        'seed': seed,
        
        # Multi-agent parameters
        'num_agents': parameters.get('num_agents', 5),
        'num_episodes': episodes,
        'max_steps': parameters.get('max_steps_per_episode', 50),
        
        # SNN parameters
        'num_neurons': parameters.get('num_neurons', 50),
        'vector_dim': parameters.get('vector_dim', 16),
        'connectivity': parameters.get('connectivity', 0.15),
        
        # Social learning
        'social_learning_freq': parameters.get('social_learning_freq', 5),
        'elite_ratio': parameters.get('elite_ratio', 0.2),
        'learner_ratio': parameters.get('learner_ratio', 0.5),
        'synapses_per_transfer': parameters.get('synapses_per_transfer', 10),
        
        # Revolution protocol
        'revolution_threshold': parameters.get('revolution_threshold', 0.5),
        'revolution_window': parameters.get('revolution_window', 5),
        'revolution_elite_ratio': parameters.get('revolution_elite_ratio', 0.1),
        
        # RL parameters
        'initial_exploration_rate': parameters.get('initial_exploration', 1.0),
        'exploration_decay': parameters.get('exploration_decay', 0.995),
        
        # Environment
        'grid_size': parameters.get('environment_config', {}).get('grid_size', 10),
        'initial_needs': parameters.get('initial_needs', [0.5, 0.5]),
        'initial_emotions': parameters.get('initial_emotions', [0.0, 0.0]),
    }
    
    try:
        # Create and run experiment
        experiment = MultiAgentExperiment(config)
        experiment.run(num_episodes=episodes)
        
        # Save metrics to output directory
        metrics_file = os.path.join(output_dir, f"run_{run_id}_metrics.json")
        
        # Copy metrics from experiment logger
        with open(metrics_file, 'w') as f:
            json.dump({
                'run_id': run_id,
                'seed': seed,
                'config': config,
                'metrics': experiment.logger.metrics_history,
                'summary': experiment.logger.get_summary()
            }, f, indent=2)
        
        return {
            "status": "COMPLETED",
            "run_id": run_id,
            "seed": seed,
            "output_csv_path": metrics_file,
            "metrics": experiment.logger.metrics_history
        }
        
    except Exception as e:
        log_error_msg = f"Run {run_id} failed: {str(e)}"
        
        # Save error info
        error_file = os.path.join(output_dir, f"run_{run_id}_error.txt")
        with open(error_file, 'w') as f:
            f.write(log_error_msg)
            f.write("\n\n")
            import traceback
            traceback.print_exc(file=f)
        
        return {
            "status": "FAILED",
            "run_id": run_id,
            "seed": seed,
            "output_csv_path": None,
            "error": str(e),
            "error_file": error_file
        }

@process(
    inputs=['domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=['domain.experiments'],
    side_effects=['filesystem.write', 'filesystem.mkdir', 'concurrency'],
    errors=['Exception']
)
def run_simulations(ctx: OrchestratorSystemContext):
    """
    Process: Run all multi-agent experiment simulations in parallel.
    
    NOTE: Updated to use MultiAgentExperiment directly (no subprocess).
    """
    log(ctx, "info", "  [Orchestration] Running multi-agent simulations (Parallel)...")
    domain = ctx.domain_ctx
    
    # Determine Max Workers
    max_workers = os.cpu_count() or 4
    log(ctx, "info", f"    [Concurrency] Max Workers: {max_workers}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_exp_run = {}

        # Loop 1: Submit Tasks
        for exp_def in domain.experiments:
            exp_output_dir = os.path.join(domain.output_dir, exp_def.name)
            os.makedirs(exp_output_dir, exist_ok=True)
            
            log(ctx, "info", f"    [Experiment: {exp_def.name}] Submitting {exp_def.runs} tasks...")

            for i in range(exp_def.runs):
                run_id = i + 1
                
                # Submit to Executor
                future = executor.submit(
                    _execute_single_run,
                    run_id=run_id,
                    exp_name=exp_def.name,
                    parameters=exp_def.parameters,
                    log_level=exp_def.log_level,
                    episodes=exp_def.episodes_per_run,
                    output_dir=exp_output_dir
                )
                
                future_to_exp_run[future] = (exp_def, run_id)

        # Loop 2: Collect Results
        for future in concurrent.futures.as_completed(future_to_exp_run):
            exp_def, run_id = future_to_exp_run[future]
            
            try:
                result = future.result()
                
                status = result["status"]
                
                # Create Record
                exp_run = ExperimentRun(
                    run_id=result["run_id"],
                    seed=result["seed"],
                    parameters=exp_def.parameters,
                    output_csv_path=result["output_csv_path"],
                    status=status
                )
                exp_def.list_of_runs.append(exp_run)
                
                if status == "COMPLETED":
                    log(ctx, "info", f"      ✅ [Experiment: {exp_def.name}] Run {run_id} Completed.")
                else:
                    err_info = result.get('error', 'Unknown')
                    log_error(ctx, f"      ❌ [Experiment: {exp_def.name}] Run {run_id} Failed: {err_info}")

            except Exception as e:
                log_error(ctx, f"CRITICAL: Future execution failed for {exp_def.name} Run {run_id}: {e}")

    log(ctx, "info", "  [Orchestration] All parallel simulations finished.")
