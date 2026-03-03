from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log, log_error
from src.orchestrator.processes.p_save_checkpoint import save_periodic_checkpoint
import numpy as np


def get_domain_ctx(ctx):
    """
    Helper to extract domain context from either:
    - Rust State (ctx.state.data["domain"] -> dict)
    - Python OrchestratorSystemContext (ctx.domain_ctx -> object)
    
    Returns the domain context and a flag indicating if it's a dict.
    """
    # Try Python dataclass style first
    try:
        if hasattr(ctx, 'domain_ctx'):
            dc = ctx.domain_ctx
            if dc is not None and hasattr(dc, 'experiments'):
                return dc, False
    except (RuntimeError, PermissionError):
        pass  # Rust isolation deepcopy failure — try other paths
    
    # Try Rust State style
    try:
        if hasattr(ctx, 'state') and hasattr(ctx.state, 'data'):
            data = ctx.state.data
            domain = data.get('domain') if hasattr(data, 'get') else getattr(data, 'domain', None)
            if domain is not None:
                return domain, isinstance(domain, dict)
    except (RuntimeError, PermissionError):
        pass
    
    # Fallback: access via internal target (bypass Rust isolation)
    try:
        target = getattr(ctx, '_target', None) or getattr(ctx, '_inner', None)
        if target is not None:
            dc = getattr(target, 'domain_ctx', None)
            if dc is not None:
                return dc, False
    except (AttributeError, RuntimeError, PermissionError):
        pass
    
    # Last resort: ctx itself might have domain_ctx accessible now
    try:
        if hasattr(ctx, 'domain_ctx'):
            return ctx.domain_ctx, False
    except RuntimeError:
        pass
    
    raise AttributeError(f"Cannot extract domain context from {type(ctx)}")


@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level', 'domain.active_experiment_episode_idx', 'domain.metrics_history'],
    outputs=['domain.metrics', 'domain.active_experiment_idx', 'domain.active_experiment_episode_idx'],
    side_effects=['env.interaction'],
    errors=[]
)
def run_single_episode(ctx: OrchestratorSystemContext):
    """
    Process: Chạy một Episode duy nhất cho tất cả Agents.
    
    Logic:
    1. Lấy Active Experiment.
    2. Chạy 1 episode (loop step).
    3. Emit signal: 'EPISODE_DONE'.
    4. Nếu đến lúc Social Learning -> Emit 'TRIGGER_SOCIAL'.
    5. Nếu xong Experiment -> Emit 'EXPERIMENT_DONE'.
    """
    domain, is_dict = get_domain_ctx(ctx)
    
    # Get event_bus (handle both dict and object)
    if is_dict:
        bus = domain.get('event_bus')
        active_exp_idx = domain.get('active_experiment_idx', 0)
        experiments = domain.get('experiments', [])
        current_episode = domain.get('active_experiment_episode_idx', 0)
    else:
        bus = domain.event_bus
        active_exp_idx = domain.active_experiment_idx
        experiments = domain.experiments
        current_episode = domain.active_experiment_episode_idx
    
    # Get Active Experiment
    if active_exp_idx >= len(experiments):
        if bus: bus.emit("ALL_EXPERIMENTS_DONE")
        return {}
    
    exp_def = experiments[active_exp_idx]
    
    # Get exp_def attributes (handle both dict and object)
    if isinstance(exp_def, dict):
        exp_name = exp_def.get('name', 'unknown')
        total_episodes = exp_def.get('episodes_per_run', 100)
    else:
        exp_name = exp_def.name
        total_episodes = exp_def.episodes_per_run
    
    # V3 MIGRATION: Fetch Runner from Runtime Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if not runner:
        log_error(ctx, f"Experiment {exp_name} not initialized (Runner not found in Registry)!")
        if bus: bus.emit("ERROR")
        return {}

    # Support resume: Skip episodes before start_episode
    start_episode = getattr(runner, 'start_episode', 0)
    if current_episode < start_episode:
        log(ctx, "info", f"⏭️  Skipping episode {current_episode} (resume starts at {start_episode})")
        if not is_dict:
            domain.active_experiment_episode_idx += 1
        if bus: bus.emit("EPISODE_DONE")
        return {}
    
    if current_episode >= total_episodes:
        # Experiment Finished
        log(ctx, "info", f"Experiment {exp_name} completed all {total_episodes} episodes.")
        
        if bus: bus.emit("EXPERIMENT_DONE")
        
        # Update state for next experiment
        return {
            'domain.active_experiment_idx': active_exp_idx + 1,
            'domain.active_experiment_episode_idx': 0
        }

    # --- EXECUTE EPISODE ---
    try:
        log(ctx, "info", f"DEBUG: Starting Episode {current_episode}")
        runner.perf_monitor.start_episode()
        metrics = runner.coordinator.run_episode(runner.env, runner.adapter)
        log(ctx, "info", f"DEBUG: Finished Episode {current_episode}")
        runner.perf_monitor.end_episode()
        
        # Episode Done (Normal)
        if bus:
            bus.emit("EPISODE_DONE")
        
        # Checkpoint Saving
        save_periodic_checkpoint(ctx)
        
        return {
            'domain.metrics': metrics
        }
    except Exception as e:
        log_error(ctx, f"Episode {current_episode} Failed: {e}")
        import traceback
        traceback.print_exc()
        if bus: bus.emit("ERROR")
    return {}
