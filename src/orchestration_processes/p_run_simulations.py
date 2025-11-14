import subprocess
import os
import json
import random
from src.experiment_context import OrchestrationContext, ExperimentRun

def p_run_simulations(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để chạy tất cả các mô phỏng cho các thử nghiệm đã định nghĩa.
    """
    print("  [Orchestration] Running simulations...")

    for exp_def in context.experiments:
        print(f"    [Experiment: {exp_def.name}] Starting {exp_def.runs} runs...")
        
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
                "--seed", str(seed)
            ]

            print(f"      [Run {run_id}/{exp_def.runs}] Executing: {' '.join(command)}")
            
            # Create ExperimentRun object and add to definition
            exp_run = ExperimentRun(
                run_id=run_id,
                seed=seed,
                parameters=exp_def.parameters,
                output_csv_path=output_csv_path,
                status="RUNNING"
            )
            exp_def.list_of_runs.append(exp_run)

            try:
                # Run main.py as a subprocess
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                exp_run.status = "COMPLETED"
                # print(result.stdout) # In ra stdout của main.py nếu cần debug
            except subprocess.CalledProcessError as e:
                exp_run.status = "FAILED"
                print(f"LỖI: Run {run_id} của thử nghiệm '{exp_def.name}' thất bại.")
                print(f"Stderr: {e.stderr}")
                print(f"Stdout (từ main.py): {e.stdout}") # Thêm dòng này để in stdout
            except Exception as e:
                exp_run.status = "FAILED"
                print(f"LỖI không xác định khi chạy Run {run_id} của thử nghiệm '{exp_def.name}': {e}")

    print("  [Orchestration] All simulations finished.")
    return context
