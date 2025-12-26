from theus import TheusEngine
from src.orchestrator.context import OrchestratorSystemContext
from src.core.context import GlobalContext, DomainContext
import os

def main():
    print("--- STARTING POST-PROCESSING ---")
    
    # Setup Context
    global_ctx = GlobalContext()
    # Manual inject config path (Theus usually handles this via CLI override)
    global_ctx.config_path = 'experiments.json'
    global_ctx.cli_log_level = 'info'
    global_ctx.settings_override = {}
    
    domain_ctx = DomainContext()
    domain_ctx.experiments = []
    domain_ctx.active_experiment_idx = 0
    domain_ctx.output_dir = "results"
    
    system_ctx = OrchestratorSystemContext(global_ctx, domain_ctx)
    
    # Setup Engine
    engine = TheusEngine(system_ctx)
    
    # Register Processes
    # We need to register p_load_config, p_aggregate_results, p_plot_results, p_analyze_data, p_save_summary
    engine.scan_and_register('src/orchestrator/processes')
    
    # Execute
    try:
        engine.execute_workflow('workflows/post_process.yaml')
        print("--- POST-PROCESSING COMPLETE ---")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
