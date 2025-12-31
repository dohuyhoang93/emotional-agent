from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log, log_error
from src.orchestrator.processes.p_save_checkpoint import save_periodic_checkpoint
import numpy as np

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'log_level', 'domain.active_experiment_episode_idx', 'domain.metrics_history'],
    outputs=['domain.metrics', 'domain.experiments', 'domain.active_experiment_episode_idx', 'domain.metrics_history'],
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
    print(f"DEBUG: [p_episode_runner] Starting Episode {current_episode}")
    # log(ctx, "info", f"Running Episode {current_episode}...")
    
    # We call internal logic of runner, but refactored to be singular
    # Using existing failed-safe wrapper method from Runner if available, 
    # OR we invoke runner.run_episode_logic()
    
    try:
        runner.perf_monitor.start_episode()
        metrics = runner.coordinator.run_episode(runner.env, runner.adapter)
        runner.perf_monitor.end_episode()
        
        # --- ENHANCE METRICS (Dashboard Phase 5) ---
        if runner.coordinator.agents:
            # 1. SNN Stats (Avg Firing Rate)
            
            for agent in runner.coordinator.agents:
                # SNN Context
                snn_ctx = agent.snn_ctx
                # Assuming 'spike_history' or similar exists. 
                # Better: Use 'metrics' from agent if available, or peek context.
                # SNN Domain Context has 'neurons' (list of Neuron objects?).
                # Let's use a simpler heuristic if deep inspection is slow.
                # Actually, agent.snn_ctx.domain_ctx.neurons is available.
                
                neurons = snn_ctx.domain_ctx.neurons
                if neurons:
                     # Calculate instantaneous firing rate (this step)
                     # Or use accumulation from episode logic?
                     # Let's rely on what 'run_episode' returns if possible.
                     # If not, we have to iterate.
                     
                     # Check if agent has gathered SNN stats?
                     pass
                     
            # 2. Maturity (Epsilon)
            # Agent 0 representative
            # Fix: RLAgent uses domain_ctx.current_exploration_rate
            agent0 = runner.coordinator.agents[0]
            epsilon = getattr(agent0.domain_ctx, 'current_exploration_rate', 0.0)
            metrics['epsilon'] = epsilon
            metrics['maturity'] = (1.0 - epsilon) * 100.0 # Scale 0-100 for gauge

            # 3. SNN Firing Rate
            # Fix: Read from SNN domain metrics (set by process_snn_cycle)
            avg_fr = 0.0
            count = 0
            for agent in runner.coordinator.agents:
                snn_metrics = agent.snn_ctx.domain_ctx.metrics
                if 'avg_firing_rate' in snn_metrics:
                     avg_fr += snn_metrics['avg_firing_rate']
                count += 1
            

            if count > 0:
                metrics['avg_firing_rate'] = avg_fr / count
            else:
                metrics['avg_firing_rate'] = 0.0

            # 4. DEBUG: Memory Leak Diagnosis (Synapse Count & Spike Queue)
            total_synapses = 0
            total_spike_queue = 0
            for agent in runner.coordinator.agents:
                snn_ctx = agent.snn_ctx
                total_synapses += len(snn_ctx.domain_ctx.synapses)
                # Correction: Sum spikes in Vectorized Buffer if active, else Dictionary
                if snn_ctx.domain_ctx.tensors.get('use_vectorized_queue', False):
                     # Buffer is (Time, N) tensor
                     total_spike_queue += np.count_nonzero(snn_ctx.domain_ctx.tensors['spike_buffer'])
                else:
                     total_spike_queue += sum(len(v) for v in snn_ctx.domain_ctx.spike_queue.values())
            
            metrics['debug_total_synapses'] = total_synapses
            metrics['debug_spike_queue_size'] = total_spike_queue
            
            # Explicit GC to mitigate leaks
            import gc
            if current_episode % 25 == 0:
                gc.collect()

        # Log & Track
        # Log & Track (POP Style: Use Domain Context)
        import datetime
        
        # Check for duplicates in DOMAIN HISTORY
        existing = [m['episode'] for m in domain.metrics_history]
        if current_episode not in existing:
             # FIX: Prevent 'metrics' from overwriting 'episode'
             # We explicitly construct the dict to ensure 'episode' is correct
             clean_metrics = metrics.copy()
             if 'episode' in clean_metrics:
                 del clean_metrics['episode'] # Remove conflicting key
                 
             metrics_entry = {
                'episode': current_episode,
                 'timestamp': datetime.datetime.now().isoformat(),
                 'metrics': clean_metrics # Nest metrics to avoid namespace pollution
             }
             
             # Also fix the argument passed to logger to match JSONL format check?
             # The new logger expects (episode, metrics).
             runner.logger.log_episode(current_episode, clean_metrics) 
             
             # Store in history (Legacy format might expect flat? Let's keep nested for safety)
             # Actually p_aggregate expects 'metrics' key or flat?
             # Let's align with Logger's JSONL format: {episode, timestamp, metrics: {...}}
             domain.metrics_history.append(metrics_entry)
        else:
             print(f"DEBUG: Skipping duplicate episode {current_episode} in metrics history.")
        
        # EXPOSE METRICS TO ORCHESTRATOR FOR DASHBOARD
        domain.metrics = metrics
        
        # Update State (POP Style)
        domain.active_experiment_episode_idx += 1
        # Sync back to runner (optional, for compatibility)
        runner.current_episode_count = domain.active_experiment_episode_idx
        
        # --- CHECK EVENTS ---
        
        # NOTE: Social Learning, Sleep Cycle, and Revolution Protocol 
        # are now orchestrated by Flux Workflow (orchestrator_flux.yaml).
        # Logic removed from here to ensure Pure POP.
        
        # Episode Done (Normal)
        if bus: 
            print(f"DEBUG: [p_episode_runner] Emitting EPISODE_DONE for Episode {current_episode}")
            bus.emit("EPISODE_DONE")
        
        # --- PERSISTENCE --- (Phase 15)
        # Checkpoint Saving
        save_periodic_checkpoint(ctx)
        
    except Exception as e:
        log_error(ctx, f"Episode {current_episode} Failed: {e}")
        if bus: bus.emit("ERROR")
