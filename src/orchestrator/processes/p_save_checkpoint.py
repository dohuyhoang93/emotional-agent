import os
from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.utils.snn_persistence import save_all_agents
from src.logger import log

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.output_dir'],
    outputs=[],
    side_effects=['filesystem.write', 'filesystem.mkdir'],
    errors=[]
)
def save_periodic_checkpoint(ctx: OrchestratorSystemContext):
    """
    Process: Save SNN Checkpoint periodically.
    """
    domain = ctx.domain_ctx
    
    # Get Runner
    if domain.active_experiment_idx >= len(domain.experiments):
        return
    exp_def = domain.experiments[domain.active_experiment_idx]
    runner = getattr(exp_def, 'runner', None)
    
    if not runner: return

    current_episode = runner.current_episode_count
    
    # Check frequency (e.g. every 50 episodes, or config based)
    save_freq = runner.config.get('checkpoint_freq', 50)
    
    if current_episode > 0 and current_episode % save_freq == 0:
        log(ctx, "info", f"  [Checkpoint] Saving snapshot at episode {current_episode}...")
        
        # Get SNN Contexts from all agents
        # Coordinator has `agents` dict {id: RLAgent}
        agents = runner.coordinator.agents
        snn_contexts = [agent.snn_ctx for agent in agents.values()]
        
        # Output Dir
        checkpoint_dir = os.path.join(runner.output_dir, f"checkpoint_ep_{current_episode}")
        
        # Save
        save_all_agents(snn_contexts, checkpoint_dir)
        log(ctx, "info", f"  [Checkpoint] Saved to {checkpoint_dir}")
