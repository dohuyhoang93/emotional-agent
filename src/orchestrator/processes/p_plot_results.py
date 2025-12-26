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

            # --- NEW PLOTS (SNN & Composition) ---

            # Extra Metrics Extraction Helper
            def get_metric(m, keys, default=0.0):
                for k in keys:
                    # Check top level
                    if k in m: return m[k]
                    # Check nested 'snn' or 'rl'
                    if 'snn' in m and isinstance(m['snn'], dict) and k in m['snn']: return m['snn'][k]
                    if 'rl' in m and isinstance(m['rl'], dict) and k in m['rl']: return m['rl'][k]
                return default

            fire_rates = [get_metric(m, ['fire_rate', 'avg_fire_rate']) for m in metrics]
            synapse_counts = [get_metric(m, ['active_synapses', 'avg_active_synapses', 'synapse_count']) for m in metrics]
            
            intrinsic = [get_metric(m, ['intrinsic_reward_total', 'avg_intrinsic_reward']) for m in metrics]
            extrinsic = [get_metric(m, ['extrinsic_reward_total', 'avg_extrinsic_reward']) for m in metrics]

            # Plot 4: SNN Physiology (Dual Axis)
            if any(fire_rates) or any(synapse_counts):
                fig, ax1 = plt.subplots(figsize=(12, 6))
                
                color = 'tab:orange'
                ax1.set_xlabel('Episode')
                ax1.set_ylabel('Fire Rate (%)', color=color)
                ax1.plot(episodes, fire_rates, color=color, label='Fire Rate')
                ax1.tick_params(axis='y', labelcolor=color)
                
                ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis
                color = 'tab:blue'
                ax2.set_ylabel('Active Synapses', color=color)
                ax2.plot(episodes, synapse_counts, color=color, linestyle='--', label='Synapses')
                ax2.tick_params(axis='y', labelcolor=color)
                
                plt.title(f'SNN Physiology - {exp_def.name}')
                fig.tight_layout()
                plt.grid(True, alpha=0.3)
                plt.savefig(os.path.join(plots_dir, f'{exp_def.name}_snn_physiology.png'), dpi=150, bbox_inches='tight')
                plt.close()

            # Plot 5: Reward Composition (Stacked)
            if any(intrinsic) or any(extrinsic):
                plt.figure(figsize=(12, 6))
                plt.stackplot(episodes, extrinsic, intrinsic, labels=['Extrinsic', 'Intrinsic'], alpha=0.6, colors=['tab:green', 'tab:purple'])
                plt.xlabel('Episode')
                plt.ylabel('Cumulative Reward')
                plt.title(f'Reward Composition (Motivation) - {exp_def.name}')
                plt.legend(loc='upper left')
                plt.grid(True, alpha=0.3)
                plt.savefig(os.path.join(plots_dir, f'{exp_def.name}_reward_composition.png'), dpi=150, bbox_inches='tight')
                plt.close()
            
            log(ctx, "info", f"  [Plotting] Plots saved for experiment '{exp_def.name}'")
            
        except Exception as e:
            log(ctx, "info", f"  [Plotting] Error generating plots for '{exp_def.name}': {e}")
    
    log(ctx, "info", f"  [Orchestration] Plots saved to {plots_dir}")
