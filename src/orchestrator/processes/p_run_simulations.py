import subprocess
import os
import json
import random
from theus import process
from src.orchestrator.context import OrchestratorSystemContext, ExperimentRun
from src.logger import log, log_error

@process(
    inputs=['domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=['domain.experiments'], # Technically inputs are mutable so we list them in outputs too if we mutate? Or just assume mutable reference. POP strictness suggests explicit output.
    side_effects=['subprocess.run', 'filesystem.write', 'filesystem.mkdir'],
    errors=['subprocess.CalledProcessError']
)
def run_simulations(ctx: OrchestratorSystemContext):
    """
    Process: Chạy tất cả các mô phỏng (Experiment Runs) thông qua subprocess.
    """
    log(ctx, "info", "  [Orchestration] Running simulations...")
    domain = ctx.domain_ctx
    
    # Iterate through experiments loaded in Domain
    for exp_def in domain.experiments:
        log(ctx, "info", f"    [Experiment: {exp_def.name}] Starting {exp_def.runs} runs (Log Level: {exp_def.log_level})...")
        
        experiment_output_dir = os.path.join(domain.output_dir, exp_def.name)
        os.makedirs(experiment_output_dir, exist_ok=True)

        for i in range(exp_def.runs):
            run_id = i + 1
            seed = random.randint(0, 1000000) 
            
            output_csv_path = os.path.join(experiment_output_dir, f"run_{run_id}.csv")
            
            # Convert parameters dict to JSON string for --settings-override
            settings_override_json = json.dumps(exp_def.parameters)

            # Construct the command to call main_v2.py
            command = [
                "python", "main_v2.py",
                "--num-episodes", str(exp_def.episodes_per_run),
                "--output-path", output_csv_path,
                "--settings-override", settings_override_json,
                "--seed", str(seed),
                "--log-level", exp_def.log_level 
            ]

            log(ctx, "info", f"      [Run {run_id}/{exp_def.runs}] Executing: {' '.join(command)}")
            
            # Create ExperimentRun object (Mutable update of Domain)
            exp_run = ExperimentRun(
                run_id=run_id,
                seed=seed,
                parameters=exp_def.parameters,
                output_csv_path=output_csv_path,
                status="RUNNING"
            )
            exp_def.list_of_runs.append(exp_run)

            stdout_log_path = os.path.join(experiment_output_dir, f"run_{run_id}_stdout.log")
            stderr_log_path = os.path.join(experiment_output_dir, f"run_{run_id}_stderr.log")

            try:
                is_visual_mode = exp_def.parameters.get("visual_mode", False)

                if is_visual_mode:
                    result = subprocess.run(command, text=True, check=True)
                else:
                    with open(stdout_log_path, 'w') as stdout_log, open(stderr_log_path, 'w') as stderr_log:
                        result = subprocess.run(
                            command, 
                            stdout=stdout_log, 
                            stderr=stderr_log, 
                            text=True, 
                            check=True
                        )
                exp_run.status = "COMPLETED"
            except subprocess.CalledProcessError:
                exp_run.status = "FAILED"
                log_error(ctx, f"Run {run_id} của thử nghiệm '{exp_def.name}' thất bại.")
                log_error(context=ctx, message=f"Kiểm tra file log lỗi để biết chi tiết: {stderr_log_path}")
            except Exception as e:
                exp_run.status = "FAILED"
                log_error(ctx, f"LỖI không xác định khi chạy Run {run_id} của thử nghiệm '{exp_def.name}': {e}")

    log(ctx, "info", "  [Orchestration] All simulations finished.")
