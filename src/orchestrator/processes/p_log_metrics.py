from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr
from src.logger import log
import datetime

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.metrics', 'domain.metrics_history', 'domain.active_experiment_episode_idx'],
    outputs=[],  # v2 compatible - no output mapping
    side_effects=['io.write'],
    errors=[]
)
def log_episode_metrics(ctx: OrchestratorSystemContext):
    """
    Process: Log the current episode metrics to file (JSONL) and update in-memory history.
    """
    domain, is_dict = get_domain_ctx(ctx)
    metrics = get_attr(domain, 'metrics', {})
    metrics_history = get_attr(domain, 'metrics_history', [])
    current_episode = get_attr(domain, 'active_experiment_episode_idx', 0)
    active_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return
    
    exp_def = experiments[active_idx]
    exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if not runner:
        return

    # Check for duplicates in DOMAIN HISTORY
    existing = [m['episode'] for m in metrics_history]
    if current_episode not in existing:
        # FIX: Prevent 'metrics' from overwriting 'episode'
        # We explicitly construct the dict to ensure 'episode' is correct
        clean_metrics = dict(metrics)
        if 'episode' in clean_metrics:
            del clean_metrics['episode']  # Remove conflicting key
            
        metrics_entry = {
            'episode': current_episode,
            'timestamp': datetime.datetime.now().isoformat(),
            'metrics': clean_metrics  # Nest metrics to avoid namespace pollution
        }
        
        # Write to disk via Runner's logger
        runner.logger.log_episode(current_episode, clean_metrics) 
        
        # Store in history (v2 mutation pattern)
        metrics_history.append(metrics_entry)
