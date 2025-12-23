import subprocess
import os
import json
import random
import concurrent.futures
from typing import Dict, Any

from theus import process
from src.orchestrator.context import OrchestratorSystemContext, ExperimentRun
from src.logger import log, log_error

def _execute_single_run(
    run_id: int,
    exp_name: str,
    parameters: Dict[str, Any],
    log_level: str,
    episodes: int,
    output_dir: str
) -> dict:
    """
    Helper function to execute a single simulation run.
    Returns a dict with result status and metadata to update the Context securely.
    """
    seed = random.randint(0, 1000000)
    output_csv_path = os.path.join(output_dir, f"run_{run_id}.csv")
    stdout_log_path = os.path.join(output_dir, f"run_{run_id}_stdout.log")
    stderr_log_path = os.path.join(output_dir, f"run_{run_id}_stderr.log")

    # Serialize overrides
    settings_override_json = json.dumps(parameters)

    command = [
        "python", "main.py",
        "--num-episodes", str(episodes),
        "--output-path", output_csv_path,
        "--settings-override", settings_override_json,
        "--seed", str(seed),
        "--log-level", log_level
    ]
    
    # Check visual mode
    is_visual_mode = parameters.get("visual_mode", False)

    try:
        if is_visual_mode:
            # If visual, we usually want to see it, so we don't capture output?
            # Or we strictly shouldn't run parallel visual.
            subprocess.run(command, text=True, check=True)
        else:
            with open(stdout_log_path, 'w') as stdout_log, open(stderr_log_path, 'w') as stderr_log:
                subprocess.run(
                    command,
                    stdout=stdout_log,
                    stderr=stderr_log,
                    text=True,
                    check=True
                )
        return {
            "status": "COMPLETED",
            "run_id": run_id,
            "seed": seed,
            "output_csv_path": output_csv_path
        }
    except subprocess.CalledProcessError:
        return {
            "status": "FAILED",
            "run_id": run_id,
            "seed": seed,
            "output_csv_path": output_csv_path,
            "error": "CalledProcessError",
            "stderr_path": stderr_log_path
        }
    except Exception as e:
        return {
            "status": "FAILED",
            "run_id": run_id,
            "seed": seed,
            "output_csv_path": output_csv_path,
            "error": str(e)
        }

@process(
    inputs=['domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=['domain.experiments'],
    side_effects=['subprocess.run', 'filesystem.write', 'filesystem.mkdir', 'concurrency'],
    errors=['subprocess.CalledProcessError']
)
def run_simulations(ctx: OrchestratorSystemContext):
    """
    Process: Chạy tất cả các mô phỏng (Experiment Runs) song song.
    """
    log(ctx, "info", "  [Orchestration] Running simulations (Parallel)...")
    domain = ctx.domain_ctx
    
    # Determine Max Workers (Defaults to CPU count + 4 for IO bound, but this is CPU bound)
    # python processes are CPU bound.
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
                
                # We need to map future back to where to store result (which ExperimentDefinition)
                future_to_exp_run[future] = (exp_def, run_id)

        # Loop 2: Collect Results as they complete
        for future in concurrent.futures.as_completed(future_to_exp_run):
            exp_def, run_id = future_to_exp_run[future]
            
            try:
                result = future.result()
                
                # Update Context (Thread-safe implicitly because we are in the main thread here getting results)
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
                    stderr = result.get('stderr_path', 'N/A')
                    log_error(ctx, f"      ❌ [Experiment: {exp_def.name}] Run {run_id} Failed: {err_info}. Log: {stderr}")

            except Exception as e:
                log_error(ctx, f"CRITICAL: Future execution failed for {exp_def.name} Run {run_id}: {e}")

    log(ctx, "info", "  [Orchestration] All parallel simulations finished.")
