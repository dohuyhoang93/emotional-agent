from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log
import datetime

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.metrics', 'domain.metrics_history', 'domain.active_experiment_episode_idx'],
    outputs=['domain.metrics_history'],
    side_effects=['io.write'],
    errors=[]
)
def log_episode_metrics(ctx: OrchestratorSystemContext):
    """
    Process: Log the current episode metrics to file (JSONL) and update in-memory history.
    """
    metrics = getattr(ctx.domain, 'metrics', {})
    metrics_history = getattr(ctx.domain, 'metrics_history', [])
    
    # Auto-cast to list if it somehow became a dict (from state hydration/serialization quirks)
    if isinstance(metrics_history, dict):
        metrics_history = list(metrics_history.values())
    elif not isinstance(metrics_history, list):
        try:
            metrics_history = list(metrics_history)
        except TypeError:
            metrics_history = [metrics_history]
            
    current_episode = getattr(ctx.domain, 'active_experiment_episode_idx', 0)
    active_idx = getattr(ctx.domain, 'active_experiment_idx', 0)
    experiments = getattr(ctx.domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {}
    
    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown')
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if not runner:
        return {}

    # Check for duplicates in DOMAIN HISTORY
    existing = [m['episode'] for m in metrics_history]
    if current_episode not in existing:
        # FIX: Prevent 'metrics' from overwriting 'episode'
        clean_metrics = dict(metrics)
        if 'episode' in clean_metrics:
            del clean_metrics['episode']
            
        metrics_entry = {
            'episode': current_episode,
            'timestamp': datetime.datetime.now().isoformat(),
            'metrics': clean_metrics
        }
        
        # Write to disk via Runner's logger
        runner.logger.log_episode(current_episode, clean_metrics) 
        
        # Store in history 
        metrics_history.append(metrics_entry)
        return {
            'domain.metrics_history': metrics_history
        }
    return {}
