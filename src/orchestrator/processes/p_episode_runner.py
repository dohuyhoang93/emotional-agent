import time
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log, log_error
from src.orchestrator.processes.p_save_checkpoint import save_periodic_checkpoint
from src.processes.snn_advanced_features_theus import process_revolution_protocol

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level'],
    outputs=['domain.metrics'],
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
    current_episode = runner.current_episode_count
    total_episodes = exp_def.episodes_per_run # Or config value
    
    if current_episode >= total_episodes:
        # Experiment Finished
        log(ctx, "info", f"Experiment {exp_def.name} completed all {total_episodes} episodes.")
        
        # Save results handled by runner or separate process?
        # Let's emit Signal
        domain.active_experiment_idx += 1
        if bus: bus.emit("EXPERIMENT_DONE")
        return

    # --- EXECUTE EPISODE ---
    # log(ctx, "info", f"Running Episode {current_episode}...")
    
    # We call internal logic of runner, but refactored to be singular
    # Using existing failed-safe wrapper method from Runner if available, 
    # OR we invoke runner.run_episode_logic()
    
    try:
        runner.perf_monitor.start_episode()
        metrics = runner.coordinator.run_episode(runner.env, runner.adapter)
        runner.perf_monitor.end_episode()
        
        # Log & Track
        runner.logger.log_episode(current_episode, metrics)
        runner.current_episode_count += 1
        
        # --- CHECK EVENTS ---
        
        
        # Social Learning Check moved to p_run_simulations.py (Orchestration Layer)

        # Sleep Cycle (Biological)
        sleep_interval = runner.config.get('sleep_interval', 25)
        sleep_duration = runner.config.get('sleep_duration', 100)
        
        if current_episode > 0 and current_episode % sleep_interval == 0:
            from src.orchestrator.processes.p_sleep_cycle import run_sleep_cycle
            run_sleep_cycle(runner.coordinator, duration=sleep_duration)


        # Revolution
        if runner.coordinator.agents:
            # Prepare contexts
            snn_global = runner.coordinator.agents[0].snn_ctx # Use first agent to access Global
            pop_contexts = [a.snn_ctx for a in runner.coordinator.agents]
            
            # Execute Process
            # Note: rl_ctx is optional now, passing None is fine as we don't collect reward here
            process_revolution_protocol(snn_global, None, pop_contexts)
            
            # Check Result
            if getattr(snn_global.domain_ctx, 'revolution_triggered', False):
                 log(ctx, "info", f"🔥 REVOLUTION TRIGGERED at Episode {current_episode}! Ancestor updated.")
                 
                 # BROADCAST ANCESTOR WEIGHTS (Phase 1 Fix)
                 new_ancestor = snn_global.domain_ctx.ancestor_weights
                 if new_ancestor:
                     for agent in runner.coordinator.agents:
                         agent.snn_ctx.domain_ctx.ancestor_weights = new_ancestor
                         
                 # Reset trigger flag
                 snn_global.domain_ctx.revolution_triggered = False 
             # In Pure FSM, we might trigger 'TRIGGER_REVOLUTION' to pause, 
             # but here we executed it synchronously inside the manager.
        
        # Episode Done (Normal)
        if bus: bus.emit("EPISODE_DONE")
        
        # --- PERSISTENCE --- (Phase 15)
        # Checkpoint Saving
        save_periodic_checkpoint(ctx)
        
    except Exception as e:
        log_error(ctx, f"Episode {current_episode} Failed: {e}")
        if bus: bus.emit("ERROR")
