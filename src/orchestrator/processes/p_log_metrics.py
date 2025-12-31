from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log
import datetime

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.metrics', 'domain.metrics_history', 'domain.active_experiment_episode_idx'],
    outputs=['domain.metrics_history'],
    side_effects=['io.write'],
    errors=[]
)
def log_episode_metrics(ctx: OrchestratorSystemContext):
    """
    Process: Log the current episode metrics to file (JSONL) and update in-memory history.
    """
    domain = ctx.domain_ctx
    metrics = domain.metrics
    
    # We use the index from context which tracks the CURRENTLY FINISHED episode
    # NOTE: In p_episode_runner, we incremented idx at end. 
    # So if we run this AFTER runner, idx is already n+1? 
    # Or should we use the one passed in? 
    # Let's check p_episode_runner logic.
    # p_episode_runner increments idx AFTER metrics calc.
    # If we split, we need to be careful about WHEN idx is incremented.
    # SAFE BET: Use 'domain.active_experiment_episode_idx' but we need to coordinate with runner.
    # Let's assume runner increments at the Very End.
    # So here 'domain.active_experiment_episode_idx' is the CURRENT one being logged.
    
    current_episode = domain.active_experiment_episode_idx
    
    # Get Runner for Logger access
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    if not runner:
        return

    # Check for duplicates in DOMAIN HISTORY
    existing = [m['episode'] for m in domain.metrics_history]
    if current_episode not in existing:
            # FIX: Prevent 'metrics' from overwriting 'episode'
            # We explicitly construct the dict to ensure 'episode' is correct
            clean_metrics = dict(metrics)
            if 'episode' in clean_metrics:
                del clean_metrics['episode'] # Remove conflicting key
                
            metrics_entry = {
            'episode': current_episode,
                'timestamp': datetime.datetime.now().isoformat(),
                'metrics': clean_metrics # Nest metrics to avoid namespace pollution
            }
            
            # Write to disk via Runner's logger
            runner.logger.log_episode(current_episode, clean_metrics) 
            
            # Store in history 
            domain.metrics_history.append(metrics_entry)
            
            # Optional: Console Log summary
            # log(ctx, "info", f"Logged Episode {current_episode}")
    else:
            pass
