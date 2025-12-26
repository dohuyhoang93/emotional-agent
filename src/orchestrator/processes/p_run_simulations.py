from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

# Import granular processes
from src.orchestrator.processes.p_initialize_experiment import initialize_active_experiment
from src.orchestrator.processes.p_episode_runner import run_single_episode

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.output_dir', 'log_level', 'domain.event_bus'],
    outputs=['domain.metrics', 'domain.active_experiment_idx'],
    side_effects=['env.interaction'],
    errors=[]
)
def run_simulations(ctx: OrchestratorSystemContext):
    """
    Process: Master Loop for Experiments.
    Iterates through all experiments and runs all episodes.
    """
    domain = ctx.domain_ctx
    
    log(ctx, "info", "Starting Simulation Loop...")
    
    while domain.active_experiment_idx < len(domain.experiments):
        # 1. Initialize Experiment
        initialize_active_experiment(ctx)
        
        # Get Runner to check completion status locally
        # (Though run_single_episode handles the logic, we need to know when to stop looping this experiment)
        # Actually run_single_episode handles ONE episode.
        # We need a loop here.
        
        exp_def = domain.experiments[domain.active_experiment_idx]
        if not hasattr(exp_def, 'runner'):
             # Should be set by initialize
             log(ctx, "error", "Runner not initialized!")
             return

        runner = exp_def.runner
        total_episodes = exp_def.episodes_per_run
        
        log(ctx, "info", f"Running '{exp_def.name}' ({total_episodes} episodes)...")
        
        while runner.current_episode_count < total_episodes:
            # Run One Episode
            run_single_episode(ctx)
            
            # === PERSIST METRICS IMMEDIATELY ===
            # This ensures we see results even if we kill the process.
            if hasattr(domain, 'metrics') and domain.metrics:
                import json
                import os
                
                # Determine file path
                output_dir = domain.output_dir
                if not output_dir:
                    output_dir = "results"
                
                # Use experiment-specific folder if available
                # Logic copied from p_save_checkpoint
                exp_name = exp_def.name
                checkpoint_dir = os.path.join(output_dir, f"{exp_name}_checkpoints")
                os.makedirs(checkpoint_dir, exist_ok=True)
                metrics_file = os.path.join(checkpoint_dir, "metrics.json")
                
                # Load existing
                existing_data = []
                if os.path.exists(metrics_file):
                    try:
                        with open(metrics_file, 'r', encoding='utf-8') as f:
                            existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []
                
                # Append new metrics
                existing_data.append({
                    "episode": runner.current_episode_count - 1, # it was incremented in run_single_episode
                    "metrics": domain.metrics
                })
                
                # Write back
                with open(metrics_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2)
                
                log(ctx, "debug", f"Saved metrics for Episode {runner.current_episode_count}")
            
            # Periodically log progress here if needed, but run_single_episode logs too.
            
        # Experiment Done (Loop finished)
        # run_single_episode handles the 'EXPERIMENT_DONE' logic internally at the start of NEXT call?
        # No, let's look at p_episode_runner.py again.
        # It says: if current >= total: incremenet idx, emit DONE.
        
        # So we call it ONE LAST TIME to trigger the "Done" logic?
        # OR we manually handle the transition here to be cleaner.
        
        # Let's manually increment here to be safe and clean.
        log(ctx, "info", f"Experiment '{exp_def.name}' Finished.")
        domain.active_experiment_idx += 1
        
    log(ctx, "info", "All Simulations Completed.")
