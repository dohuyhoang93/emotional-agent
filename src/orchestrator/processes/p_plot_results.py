import matplotlib.pyplot as plt
import os
from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def plot_results(ctx: OrchestratorSystemContext):
    """
    Process: Generate plots for multi-agent experiments.
    
    NOTE: Updated to handle JSON metrics and multi-agent specific plots.
    """
    log(ctx, "info", "  [Orchestration] Plotting aggregated results...")
    domain = ctx.domain_ctx
    
    plots_dir = os.path.join(domain.output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    log(ctx, "info", "  [Plotting] Generating aggregated plots...")
    
    for exp_def in domain.experiments:
        if not exp_def.aggregated_data:
            log(ctx, "info", f"  [Plotting] No data for experiment '{exp_def.name}', skipping plots.")
            continue
        
        try:
            metrics = exp_def.aggregated_data
            
            # Extract data
            episodes = [m.get('episode', 0) for m in metrics]
            avg_rewards = [m.get('avg_reward', 0.0) for m in metrics]
            best_rewards = [m.get('best_reward', 0.0) for m in metrics]
            social_transfers = [m.get('social_learning_transfers', 0) for m in metrics]
            revolutions = [m.get('revolutions', 0) for m in metrics]
            
            # Plot 1: Reward curves
            plt.figure(figsize=(12, 6))
            plt.plot(episodes, avg_rewards, label='Avg Reward', alpha=0.7)
            plt.plot(episodes, best_rewards, label='Best Reward', alpha=0.7)
            plt.xlabel('Episode')
            plt.ylabel('Reward')
            plt.title(f'Learning Curve - {exp_def.name}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            plt.savefig(os.path.join(plots_dir, f'{exp_def.name}_rewards.png'), dpi=150, bbox_inches='tight')
            plt.close()
            
            # Plot 2: Social learning activity
            if any(social_transfers):
                plt.figure(figsize=(12, 6))
                plt.bar(episodes, social_transfers, alpha=0.7, color='green')
                plt.xlabel('Episode')
                plt.ylabel('Social Learning Transfers')
                plt.title(f'Social Learning Activity - {exp_def.name}')
                plt.grid(True, alpha=0.3)
                plt.savefig(os.path.join(plots_dir, f'{exp_def.name}_social_learning.png'), dpi=150, bbox_inches='tight')
                plt.close()
            
            # Plot 3: Revolution events
            if any(revolutions):
                plt.figure(figsize=(12, 6))
                plt.bar(episodes, revolutions, alpha=0.7, color='red')
                plt.xlabel('Episode')
                plt.ylabel('Revolutions')
                plt.title(f'Revolution Protocol Activity - {exp_def.name}')
                plt.grid(True, alpha=0.3)
                plt.savefig(os.path.join(plots_dir, f'{exp_def.name}_revolutions.png'), dpi=150, bbox_inches='tight')
                plt.close()
            
            log(ctx, "info", f"  [Plotting] Plots saved for experiment '{exp_def.name}'")
            
        except Exception as e:
            log(ctx, "info", f"  [Plotting] Error generating plots for '{exp_def.name}': {e}")
    
    log(ctx, "info", f"  [Orchestration] Plots saved to {plots_dir}")
