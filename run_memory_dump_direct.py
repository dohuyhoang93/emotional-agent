import sys
import os
import json

# Ensure path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.orchestrator.context import ExperimentDefinition, OrchestratorDomainContext
from src.orchestrator.processes.p_initialize_experiment import FSMExperimentRunner
from src.utils.snn_persistence import save_snn_agent

def main():
    print("--- DIRECT MEMORY DUMP RUN ---")
    
    # 1. Load Config
    with open("experiments_memory_dump.json", "r") as f:
        config = json.load(f)
        
    exp_config = config["experiments"][0]
    params = exp_config["parameters"]
    
    # 2. Create Definition
    exp_def = ExperimentDefinition(
        name="direct_dump",
        runs=1,
        episodes_per_run=1,
        parameters=params,
        log_level="info"
    )
    
    # 3. Create Runner
    print("Initializing Runner...")
    output_dir = "results/direct_dump"
    os.makedirs(output_dir, exist_ok=True)
    runner = FSMExperimentRunner(exp_def.parameters, output_dir)
    
    # 4. Initialize Run
    print("Initializing Run 0...")
    # Mock Global/Domain context for logger?
    # FSMExperimentRunner init creates inline Logger which prints to stdout? 
    # Yes, I implemented inline Logger.
    
    runner.initialize_run(0)
    
    # 5. Run Episode
    print("Running Episode 0...")
    runner.run_episode(0)
    
    # 6. Save Memory
    print("Saving Memory...")
    output_dir = "results/direct_dump"
    os.makedirs(output_dir, exist_ok=True)
    
    agent = runner.coordinator.agents[0]
    save_path = os.path.join(output_dir, "agent_0_dump.pkl")
    
    # save_snn_agent expects (agent_obj, filepath, rl_ctx)
    save_snn_agent(agent, save_path, agent.rl_ctx)
    
    print(f"Memory Dump Saved to {save_path}")
    print("--- DONE ---")

if __name__ == "__main__":
    main()
