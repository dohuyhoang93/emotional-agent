import subprocess
import os
import json
import random
from src.experiment_context import OrchestrationContext, ExperimentRun
from src.logger import log, log_error # Import the new logger

def p_run_simulations(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để chạy tất cả các mô phỏng cho các thử nghiệm đã định nghĩa.
    """
    log(context, "info", "  [Orchestration] Running simulations...")

    for exp_def in context.experiments:
        log(context, "info", f"    [Experiment: {exp_def.name}] Starting {exp_def.runs} runs (Log Level: {exp_def.log_level})...")
        
        experiment_output_dir = os.path.join(context.global_output_dir, exp_def.name)
        os.makedirs(experiment_output_dir, exist_ok=True)

        for i in range(exp_def.runs):
            run_id = i + 1
            seed = random.randint(0, 1000000) # Generate a random seed for each run
            
            output_csv_path = os.path.join(experiment_output_dir, f"run_{run_id}.csv")
            
            # Convert parameters dict to JSON string for --settings-override
            settings_override_json = json.dumps(exp_def.parameters)

            # Construct the command to call main.py
            command = [
                "python", "main.py",
                "--num-episodes", str(exp_def.episodes_per_run),
                "--output-path", output_csv_path,
                "--settings-override", settings_override_json,
                "--seed", str(seed),
                "--log-level", exp_def.log_level # Pass the log_level to main.py
            ]

            log(context, "info", f"      [Run {run_id}/{exp_def.runs}] Executing: {' '.join(command)}")
            
            # Create ExperimentRun object and add to definition
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
                # Chạy main.py và chuyển hướng output vào file log
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
                log_error(context, f"Run {run_id} của thử nghiệm '{exp_def.name}' thất bại.")
                log_error(context, f"Kiểm tra file log lỗi để biết chi tiết: {stderr_log_path}")
            except Exception as e:
                exp_run.status = "FAILED"
                log_error(context, f"LỖI không xác định khi chạy Run {run_id} của thử nghiệm '{exp_def.name}': {e}")

    log(context, "info", "  [Orchestration] All simulations finished.")
    return context
