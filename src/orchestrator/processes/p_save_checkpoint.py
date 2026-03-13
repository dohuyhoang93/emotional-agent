import os
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr
from src.utils.snn_persistence import save_all_agents
from src.logger import log

@process(
    inputs=['domain', 'domain_ctx', 'domain_ctx.active_experiment_idx', 'domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=[],  # v2 compatible - no output mapping
    side_effects=['filesystem.write', 'filesystem.mkdir'],
    errors=[]
)
def save_periodic_checkpoint(ctx: OrchestratorSystemContext):
    """
    Process: Save SNN Checkpoint periodically.
    """
    domain, is_dict = get_domain_ctx(ctx)
    
    # Get experiment info (handle both dict and object)
    active_idx = get_attr(domain, 'active_experiment_idx', 0)
    experiments = get_attr(domain, 'experiments', [])
    
    if active_idx >= len(experiments):
        return {}
    
    exp_def = experiments[active_idx]
    exp_name = get_attr(exp_def, 'name', 'unknown') if isinstance(exp_def, dict) else exp_def.name
    
    # V3 MIGRATION: Fetch Runner from Registry
    from src.orchestrator.runtime_registry import get_runner
    runner = get_runner(exp_name)
    
    if not runner: return {}

    current_episode = runner.current_episode_count
    
    # Check frequency (e.g. every 50 episodes, or config based)
    save_freq = runner.config.get('checkpoint_freq', 50)
    
    if current_episode > 0 and current_episode % save_freq == 0:
        log(ctx, "info", f"  [Checkpoint] Saving snapshot at episode {current_episode}...")
        
        # Get Contexts from all agents
        # Coordinator has `agents` list [RLAgent, ...]
        agents = runner.coordinator.agents
        snn_contexts = [agent.snn_ctx for agent in agents]
        rl_contexts = [agent.rl_ctx for agent in agents]
        
        # Output Dir
        checkpoint_dir = os.path.join(runner.output_dir, f"checkpoint_ep_{current_episode}")
        
        # Save (V3: Pass rl_contexts to enable Neural Brain checkpoints)
        save_all_agents(snn_contexts, checkpoint_dir, agents_rl_contexts=rl_contexts)
        log(ctx, "info", f"  [Checkpoint] Saved to {checkpoint_dir}")
