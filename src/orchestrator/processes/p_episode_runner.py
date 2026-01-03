from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log, log_error
from src.orchestrator.processes.p_save_checkpoint import save_periodic_checkpoint
import numpy as np

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level', 'domain.active_experiment_episode_idx', 'domain.metrics_history'],
    outputs=['domain', 'domain_ctx', 'domain.metrics', 'domain.experiments', 'domain.active_experiment_episode_idx', 'domain.metrics_history'],
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
    domain = ctx.domain_ctx
    bus = domain.event_bus
    
    # Get Active Experiment
    if domain.active_experiment_idx >= len(domain.experiments):
        if bus: bus.emit("ALL_EXPERIMENTS_DONE")
        return

    exp_def = domain.experiments[domain.active_experiment_idx]
    
    # Check if experiment is initialized (Experiment State needs to be persistent)
    # NOTE: In Pure POP, state should be in Context. 
    # Here we assume 'exp_def.runtime_state' holds the MultiAgentExperiment instance.
    # Check p_initialize_experiment.py for setup.
    
    runner = getattr(exp_def, 'runner', None)
    if not runner:
        log_error(ctx, f"Experiment {exp_def.name} not initialized!")
        if bus: bus.emit("ERROR")
        return

    # Run ONE Episode
    # POP Fix: Use context state instead of Runner object state
    current_episode = domain.active_experiment_episode_idx
    total_episodes = exp_def.episodes_per_run # Or config value
    
    if current_episode >= total_episodes:
        # Experiment Finished
        log(ctx, "info", f"Experiment {exp_def.name} completed all {total_episodes} episodes.")
        
        # Save results handled by runner or separate process?
        # Let's emit Signal
        # Let's emit Signal
        domain.active_experiment_idx += 1
        # POP Fix: Reset episode count for next experiment
        domain.active_experiment_episode_idx = 0
        
        if bus: bus.emit("EXPERIMENT_DONE")
        return

    # --- EXECUTE EPISODE ---
    
    # We call internal logic of runner, but refactored to be singular
    # Using existing failed-safe wrapper method from Runner if available, 
    # OR we invoke runner.run_episode_logic()
    
    try:
        runner.perf_monitor.start_episode()
        metrics = runner.coordinator.run_episode(runner.env, runner.adapter)
        runner.perf_monitor.end_episode()
        
        # EXPOSE METRICS TO ORCHESTRATOR FOR DASHBOARD (Basic only)
        # Detailed enrichment happens in p_enrich_metrics.py
        domain.metrics = metrics
        
        # NOTE: State update (increment episode) moved to p_advance_episode.py
        # NOTE: Logging moved to p_log_metrics.py
        
        # --- CHECK EVENTS ---
        
        # Garbage Collection (Safety)
        import gc
        if current_episode % 25 == 0:
            gc.collect()
        
        # --- CHECK EVENTS ---
        
        # NOTE: Social Learning, Sleep Cycle, and Revolution Protocol 
        # are now orchestrated by Flux Workflow (orchestrator_flux.yaml).
        # Logic removed from here to ensure Pure POP.
        
        # Episode Done (Normal)
        if bus:
            bus.emit("EPISODE_DONE")
        
        # --- PERSISTENCE --- (Phase 15)
        # Checkpoint Saving
        save_periodic_checkpoint(ctx)
        
    except Exception as e:
        log_error(ctx, f"Episode {current_episode} Failed: {e}")
        if bus: bus.emit("ERROR")
