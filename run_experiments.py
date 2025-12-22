import argparse
import sys
import os

from theus import TheusEngine
from src.orchestrator.context import (
    OrchestratorGlobalContext, 
    OrchestratorDomainContext, 
    OrchestratorSystemContext
)

# Import Processes
# Import Processes (Auto-Discovered)

from src.logger import log, log_error

def main(argv=None):
    parser = argparse.ArgumentParser(description="DeepSearch Agent - Orchestration Layer (POP)")
    parser.add_argument(
        '--config',
        type=str,
        default='experiments.json',
        help='Path to experiment config JSON.'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['silent', 'info', 'verbose'],
        default=None,
        help='Override log level.'
    )
    args = parser.parse_args(argv)

    # 1. Initialize Contexts (3-Layer)
    global_ctx = OrchestratorGlobalContext(
        config_path=args.config,
        cli_log_level=args.log_level
    )
    
    domain_ctx = OrchestratorDomainContext(
        output_dir="results", # Default, updated by p_load_config
        effective_log_level="info" # Default
    )
    
    system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)

    # 2. Initialize Engine
    # Note: Orchestrator might arguably NOT use strict mode if it just does IO, 
    # but for V2 compliance we enable it.
    engine = TheusEngine(system_ctx, strict_mode=True)
    
    # 3. Auto-Discovery
    engine.scan_and_register("src/orchestrator/processes")
    
    log(system_ctx, "info", "--- STARTING ORCHESTRATION WORKFLOW (POP) ---")
    
    # 4. Execute Workflow (Synchronous List for Simplicity)
    # Replicating main_v2.py pattern instead of loading YAML which ExecuteWorkflow does implicitly.
    # Assuming standard orchestration steps
    workflow_steps = [
        "load_config",
        "run_simulations",
        "aggregate_results",
        "plot_results",
        "analyze_data",
        "save_summary"
    ]
    
    try:
        if hasattr(engine, 'execute_process'):
             runner = engine.execute_process # SDK v1 naming?
        else:
             runner = engine.run_process # SDK v2 naming confirmed in main_v2.py
             
        for step in workflow_steps:
             if hasattr(engine, 'run_process'):
                 engine.run_process(step)
             else:
                 engine.execute_process(step)
        
        # Check Final Report
        if "LỖI" in system_ctx.domain_ctx.final_report:
             log_error(system_ctx, "Workflow finished with errors reported.")
             sys.exit(1)
             
        log(system_ctx, "info", "--- ORCHESTRATION FINISHED ---")
        return system_ctx
        
    except Exception as e:
        log_error(system_ctx, f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
