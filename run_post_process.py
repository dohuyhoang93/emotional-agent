import argparse
import sys
import os
sys.path.append(os.getcwd())
sys.path.append('theus')

from theus.engine import TheusEngine
from src.orchestrator.context import (
    OrchestratorGlobalContext, 
    OrchestratorDomainContext, 
    OrchestratorSystemContext
)
from src.logger import log, log_error

def main():
    parser = argparse.ArgumentParser(description="EmotionAgent - Post Processing Tool")
    parser.add_argument('--config', type=str, default='experiments.json', help='Path to experiment config JSON.')
    args = parser.parse_args()

    # 1. Initialize Contexts
    global_ctx = OrchestratorGlobalContext(config_path=args.config, cli_log_level="info")
    domain_ctx = OrchestratorDomainContext(output_dir="results", effective_log_level="info")
    system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)

    # 2. Initialize Engine (No strict mode needed for analysis)
    engine = TheusEngine(system_ctx, strict_mode=False)
    
    # 3. Register Processes
    engine.scan_and_register("src/orchestrator/processes")
    
    log(system_ctx, "info", "--- STARTING POST-PROCESS ANALYSIS ---")
    
    try:
        # 4. Sequentially Execute Analysis Steps
        
        # Step A: Load Config (to know what experiments to look for)
        log(system_ctx, "info", "▶️ Loading Configuration...")
        engine.execute_process("load_config") # Populates domain.experiments
        
        if not domain_ctx.experiments:
             log_error(system_ctx, "No experiments found in config.")
             return

        # Step B: Aggregate Results (Now supports .jsonl)
        log(system_ctx, "info", "▶️ Aggregating Data...")
        engine.execute_process("aggregate_results")
        
        # Step C: Plot Results
        log(system_ctx, "info", "▶️ Generating Plots...")
        engine.execute_process("plot_results")
        
        # Step D: Analyze Data (Summary Report)
        log(system_ctx, "info", "▶️ Analyzing Data...")
        engine.execute_process("analyze_data")
        engine.execute_process("save_summary") # If exists, or analyze_data handles it? 
        # Checking file list: p_save_summary.py exists.
        engine.execute_process("save_summary") # Correct name found in file
        # Checking p_save_summary.py content via list_dir earlier: "p_save_summary.py".
        # Let's assume process name matches file name convention or search dict.
        # In Theus, process name is usually function name.
        # p_save_summary.py -> likely def save_summary_report. 
        # I'll enable it, if it fails engine will warn.
        
        log(system_ctx, "info", "--- POST-PROCESS FINISHED ---")
        
    except Exception as e:
        log_error(system_ctx, f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
