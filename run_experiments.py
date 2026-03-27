import argparse
import os
import sys

# V3 Fix: Ensure project root is in path for Threaded Execution imports
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from theus.engine import TheusEngine
from src.orchestrator.context import (
    OrchestratorGlobalContext, 
    OrchestratorDomainContext, 
    OrchestratorSystemContext
)

# Import Processes
# Import Processes (Auto-Discovered)

from src.logger import log, log_error

def main(argv=None):
    parser = argparse.ArgumentParser(description="EmotionAgent - Orchestration Layer (POP)")
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
    parser.add_argument(
        '--settings-override',
        type=str,
        default=None,
        help='JSON string to override experiment parameters globally (and max_episodes).'
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        help='Run in headless mode (Disable UI/Visualization).'
    )
    # Resume arguments
    parser.add_argument(
        '--resume',
        type=str,
        default=None,
        help='Checkpoint path to resume from.'
    )
    parser.add_argument(
        '--start-episode',
        type=int,
        default=0,
        help='Episode number to resume from.'
    )
    parser.add_argument(
        '--max-episodes',
        type=int,
        default=None,
        help='Override maximum episodes to run.'
    )
    
    args = parser.parse_args(argv)

    # V3 Optimization: Auto-silent in headless mode if not specified
    if args.headless and args.log_level is None:
        args.log_level = 'silent'
        # Inform the user once that we are entering silent mode
        print("\n  [Headless Mode] Silent execution enabled. Terminal logs suppressed.")
        print("  [Headless Mode] Workflow progress will be logged to: logs/audit.log\n")

    # Construct Settings Override
    override_dict = {}
    if args.settings_override:
        import json
        try:
            override_dict = json.loads(args.settings_override)
        except:
            print(f"Error parsing --settings-override: {args.settings_override}")
            
    if args.resume:
        override_dict['checkpoint_path'] = args.resume
    if args.start_episode > 0:
        override_dict['start_episode'] = args.start_episode
    if args.max_episodes is not None:
        override_dict['max_episodes'] = args.max_episodes
        
    import json
    settings_override_json = json.dumps(override_dict) if override_dict else None

    # 1. Initialize Contexts (3-Layer)
    global_ctx = OrchestratorGlobalContext(
        config_path=args.config,
        cli_log_level=args.log_level,
        settings_override=settings_override_json,
        log_level=args.log_level if args.log_level else "info"
    )
    # Inject headless flag
    global_ctx.headless = args.headless
    
    domain_ctx = OrchestratorDomainContext(
        output_dir="results", # Default, updated by p_load_config
        effective_log_level=args.log_level if args.log_level else "info"
    )
    
    system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)

    # 1.5. Configure Logging & Audit
    import logging
    from theus.config import ConfigFactory
    
    # Configure logging to file for Audit Review
    # Configure logging to file for Audit Review
    os.makedirs('logs', exist_ok=True)
    logging.basicConfig(
        filename=os.path.join('logs', 'audit.log'),
        filemode='w',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    # Suppress TheusEngine noise in Audit Log (High frequency workflow execution)
    logging.getLogger("TheusEngine").setLevel(logging.WARNING)
    
    # Load Audit Recipe
    audit_recipe = None
    if os.path.exists("specs/multi_agent_audit.yaml"):
        try:
            log(global_ctx, "info", "✅ Loading Multi-Agent Audit Recipe...")
            audit_recipe = ConfigFactory.load_recipe("specs/multi_agent_audit.yaml")
        except Exception as e:
            log_error(global_ctx, f"Failed to load Audit Recipe: {e}")

    # 2. Initialize Engine
    # V3 Migration: strict_guards is native to Rust Core (Process Isolation).
    # Memory Leak issues from V2 are resolved by Arc<T> Zero-Copy.
    engine = TheusEngine(
        context=system_ctx, 
        strict_guards=False, # Disabled for Legacy Process Compatibility
        audit_recipe=audit_recipe,
        write_timeout_ms=3600000 # 60 phút: SNN cycle đầy đủ cần nhiều thời gian hơn 10 phút cũ

    )
    
    # 3. Auto-Discovery
    engine.scan_and_register("src/orchestrator/processes")
    engine.scan_and_register("src/processes")
    
    # Manual Registration (Fallback) - REMOVED
    # Fixed underlying ImportErrors and improved Engine logging
    # engine.scan_and_register should now work or report errors.

    log(system_ctx, "info", "--- STARTING ORCHESTRATION WORKFLOW ---")
    
    # 4. Execute Workflow (Declarative Flux)
    try:
        import asyncio
        asyncio.run(engine.execute_workflow("workflows/orchestrator_flux.yaml", max_ops=1000000))
        
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
