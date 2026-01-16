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
    
    # V3 MIGRATION: Fetch Runner from Runtime Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_def.name)
    
    if not runner:
        log_error(ctx, f"Experiment {exp_def.name} not initialized (Runner not found in Registry)!")
        if bus: bus.emit("ERROR")
        return

    # Run ONE Episode
    # POP Fix: Use context state instead of Runner object state
    current_episode = domain.active_experiment_episode_idx
    total_episodes = exp_def.episodes_per_run # Or config value
    
    # Support resume: Skip episodes before start_episode
    start_episode = getattr(runner, 'start_episode', 0)
    if current_episode < start_episode:
        log(ctx, "info", f"⏭️  Skipping episode {current_episode} (resume starts at {start_episode})")
        domain.active_experiment_episode_idx += 1
        if bus: bus.emit("EPISODE_DONE")
        return
    
    if current_episode >= total_episodes:
        # Experiment Finished
        log(ctx, "info", f"Experiment {exp_def.name} completed all {total_episodes} episodes.")
        
        # Save results handled by runner or separate process?
        # Let's emit Signal
        # Experiment Finished
        log(ctx, "info", f"Experiment {exp_def.name} completed all {total_episodes} episodes.")
        
        # Save results handled by runner or separate process?
        # Let's emit Signal
        
        if bus: bus.emit("EXPERIMENT_DONE")
        
        # V3 MIGRATION: Return updates for Experiment Switching
        from dataclasses import replace
        new_domain = replace(domain, 
                             active_experiment_idx=domain.active_experiment_idx + 1,
                             active_experiment_episode_idx=0)
        
        return {"domain_ctx": new_domain}

    # --- EXECUTE EPISODE ---
    
    # We call internal logic of runner, but refactored to be singular
    # Using existing failed-safe wrapper method from Runner if available, 
    # OR we invoke runner.run_episode_logic()
    
    try:
        log(ctx, "info", f"DEBUG: Starting Episode {current_episode}")
        runner.perf_monitor.start_episode()
        metrics = runner.coordinator.run_episode(runner.env, runner.adapter)
        log(ctx, "info", f"DEBUG: Finished Episode {current_episode}")
        runner.perf_monitor.end_episode()
        
        # EXPOSE METRICS TO ORCHESTRATOR FOR DASHBOARD (Basic only)
        # Detailed enrichment happens in p_enrich_metrics.py
        
        # NOTE: State update (increment episode) moved to p_advance_episode.py
        # NOTE: Logging moved to p_log_metrics.py
        
        # --- CHECK EVENTS ---
        
        # Garbage Collection (Safety)
        import gc
        if current_episode % 25 == 0:
            gc.collect()
        
        # --- CHECK EVENTS ---
        
        # Episode Done (Normal)
        if bus:
            bus.emit("EPISODE_DONE")
        
        # --- PERSISTENCE --- (Phase 15)
        # Checkpoint Saving
        save_periodic_checkpoint(ctx)
        
        # V3 MIGRATION: Return updates
        # domain.metrics = metrics -> Return "domain_ctx": replace(domain, metrics=metrics)
        # But wait, domain_ctx is a complex object.
        # TheusEngine V3 usually expects "domain" key to update the domain.
        # However, checking `src/orchestrator/context.py`, OrchestratorSystemContext has `domain_ctx`.
        # Theus Engine context mapping from engine.py:
        # data["domain"] = context.domain_ctx
        # So return {"domain": new_domain_obj} is correct.
        
        from dataclasses import replace
        new_domain = replace(domain, metrics=metrics) # Only update metrics here
        
        return {"domain_ctx": new_domain}
        
    except Exception as e:
        log_error(ctx, f"Episode {current_episode} Failed: {e}")
        if bus: bus.emit("ERROR")
        return {}
