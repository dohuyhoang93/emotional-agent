import argparse
import sys
import os

from src.core.engine import POPEngine
from src.orchestrator.context import (
    OrchestratorGlobalContext, 
    OrchestratorDomainContext, 
    OrchestratorSystemContext
)

# Import Processes
from src.orchestrator.processes.p_load_config import load_config
from src.orchestrator.processes.p_run_simulations import run_simulations
from src.orchestrator.processes.p_aggregate_results import aggregate_results
from src.orchestrator.processes.p_plot_results import plot_results
from src.orchestrator.processes.p_analyze_data import analyze_data
from src.orchestrator.processes.p_save_summary import save_summary

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
    
    system_ctx = OrchestratorSystemContext(global_ctx, domain_ctx)

    # 2. Initialize Engine
    engine = POPEngine(system_ctx)
    
    # 3. Register Processes
    engine.register_process("load_config", load_config)
    engine.register_process("run_simulations", run_simulations)
    engine.register_process("aggregate_results", aggregate_results)
    engine.register_process("plot_results", plot_results)
    engine.register_process("analyze_data", analyze_data)
    engine.register_process("save_summary", save_summary)
    
    log(system_ctx, "info", "--- STARTING ORCHESTRATION WORKFLOW (POP) ---")
    
    # 4. Execute Workflow
    try:
        final_ctx = engine.execute_workflow("workflows/orchestration_workflow.yaml")
        
        # Check Final Report for errors (Primitive error handling logic via report string)
        if hasattr(final_ctx, 'domain_ctx') and hasattr(final_ctx.domain_ctx, 'final_report') and "LỖI" in final_ctx.domain_ctx.final_report:
             log_error(final_ctx, "Workflow finished with errors reported.")
             # We might exit code 1 here if strict
             
        log(final_ctx, "info", "--- ORCHESTRATION FINISHED ---")
        return final_ctx
        
    except Exception as e:
        log_error(system_ctx, f"CRITICAL FAILURE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()