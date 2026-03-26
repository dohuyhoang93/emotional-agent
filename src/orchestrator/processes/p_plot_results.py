import matplotlib
# NOTE: Force non-interactive backend — this process runs on a worker
# thread (asyncio.to_thread via Flux), so tkinter GUI would crash.
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain_ctx', 'domain', 'domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def plot_results(ctx: OrchestratorSystemContext):
    """
    Process: Generate plots for multi-agent experiments (Aesthetic Upgrade).
    """
    log(ctx, "info", "  [Orchestration] Plotting aggregated results (Enhanced)...")
    
    output_dir = getattr(ctx.domain, 'output_dir', 'results')
    plots_dir = os.path.join(output_dir, "plots")
    os.makedirs(plots_dir, exist_ok=True)
    
    # Set Style
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
    except:
        plt.style.use('ggplot')

    experiments = getattr(ctx.domain, 'experiments', [])
    for exp_def in experiments:
        exp_name = getattr(exp_def, 'name', 'unknown')
        aggregated_data = getattr(exp_def, 'aggregated_data', [])
        # NOTE: aggregated_data có thể là ContextGuard wrapping list/DataFrame,
        # dùng len() thay vì truth test để tránh ValueError từ pandas DataFrame.
        try:
            has_data = len(aggregated_data) > 0
        except (TypeError, ValueError):
            has_data = False
        if not has_data:
            log(ctx, "info", f"  [Plotting] No data for experiment '{exp_name}', skipping plots.")
            continue
        
        try:
            metrics = aggregated_data
            
            # Helper to safely extract lists
            def get_series(key, default=0.0):
                return [m.get(key, default) for m in metrics]

            episodes = [m.get('episode', i) for i, m in enumerate(metrics)]
            
            # Create DataFrame for easy smoothing
            df = pd.DataFrame(metrics)
            # Ensure episode col exists
            if 'episode' not in df.columns:
                df['episode'] = episodes
            
            # Define window for smoothing (5% of total episodes or min 10)
            window = max(10, int(len(df) * 0.05))
            
            # --- Plot 1: Reward Curves (Raw + Smooth) ---
            avg_rewards = df['avg_reward'] if 'avg_reward' in df else pd.Series([0]*len(df))
            best_rewards = df['best_reward'] if 'best_reward' in df else pd.Series([0]*len(df))
            
            plt.figure(figsize=(14, 7))
            
            # Avg Reward: Raw (Faint) + Smooth (Bold)
            plt.plot(episodes, avg_rewards, alpha=0.15, color='tab:blue', label='_nolegend_')
            plt.plot(episodes, avg_rewards.rolling(window=window).mean(), color='tab:blue', linewidth=2.5, label=f'Avg Reward (MA-{window})')
            
            # Best Reward: Smooth Only
            plt.plot(episodes, best_rewards.rolling(window=window).mean(), color='tab:orange', linewidth=2, linestyle='--', label=f'Best Reward (MA-{window})')
            
            plt.xlabel('Episode', fontsize=12)
            plt.ylabel('Reward', fontsize=12)
            plt.title(f'Learning Curve: {exp_name}', fontsize=14, fontweight='bold')
            plt.legend(frameon=True, fancybox=True, framealpha=0.9)
            plt.tight_layout()
            plt.savefig(os.path.join(plots_dir, f'{exp_name}_rewards.png'), dpi=200)
            plt.close()
            
            # --- Plot 2: Social & Revolution (Combined Event Plot) ---
            social = df.get('social_learning_transfers', pd.Series([0]*len(df)))
            revolution = df.get('revolutions', pd.Series([0]*len(df)))
            
            if social.sum() > 0 or revolution.sum() > 0:
                plt.figure(figsize=(14, 6))
                if social.sum() > 0:
                    plt.bar(episodes, social, alpha=0.6, color='tab:green', label='Social Transfers')
                if revolution.sum() > 0:
                    rev_indices = [i for i, x in enumerate(revolution) if x > 0]
                    if rev_indices:
                         for rev_idx in rev_indices:
                             plt.axvline(x=episodes[rev_idx], color='tab:red', linestyle=':', alpha=0.8, ymin=0, ymax=1)
                         # Add dummy handle
                         plt.plot([], [], color='tab:red', linestyle=':', label='Revolution Event')

                plt.xlabel('Episode')
                plt.ylabel('Count')
                plt.title(f'Social Dynamics: {exp_name}', fontsize=14)
                plt.legend()
                plt.tight_layout()
                plt.savefig(os.path.join(plots_dir, f'{exp_name}_social_dynamics.png'), dpi=200)
                plt.close()

            # --- Plot 3: SNN Physiology ---
            fire_cols = [c for c in df.columns if 'fire_rate' in c]
            syn_cols = [c for c in df.columns if 'synapse' in c and 'count' in c or 'active_synapses' in c]
            
            if fire_cols and syn_cols:
                fr = df[fire_cols[0]]
                syn = df[syn_cols[0]]
                
                fig, ax1 = plt.subplots(figsize=(14, 7))
                
                # Fire Rate
                color = 'tab:purple'
                ax1.set_xlabel('Episode')
                ax1.set_ylabel('Avg Fire Rate (%)', color=color, fontweight='bold')
                ax1.plot(episodes, fr.rolling(window=window).mean(), color=color, linewidth=2)
                ax1.tick_params(axis='y', labelcolor=color)
                
                # Synapses
                ax2 = ax1.twinx()
                color = 'tab:cyan'
                ax2.set_ylabel('Active Synapses', color=color, fontweight='bold')
                ax2.plot(episodes, syn, color=color, linewidth=2, linestyle='--', alpha=0.8)
                ax2.tick_params(axis='y', labelcolor=color)
                
                plt.title(f'SNN Composition: {exp_name}', fontsize=14)
                plt.tight_layout()
                plt.savefig(os.path.join(plots_dir, f'{exp_name}_snn_physiology.png'), dpi=200)
                plt.close()

            # --- Plot 4: Success Rate (if available) ---
            if 'success_rate' in df.columns:
                 plt.figure(figsize=(14, 6))
                 sr = df['success_rate']
                 plt.plot(episodes, sr, alpha=0.2, color='tab:green')
                 plt.plot(episodes, sr.rolling(window=window).mean(), color='tab:green', linewidth=2.5, label=f'Success Rate (MA-{window})')
                 plt.fill_between(episodes, 0, sr.rolling(window=window).mean(), color='tab:green', alpha=0.1)
                 
                 plt.ylim(0, 1.05)
                 plt.xlabel('Episode')
                 plt.ylabel('Success Rate')
                 plt.title(f'Performance Stability: {exp_name}', fontsize=14)
                 plt.legend()
                 plt.tight_layout()
                 plt.savefig(os.path.join(plots_dir, f'{exp_name}_success_rate.png'), dpi=200)
                 plt.close()

            log(ctx, "info", f"  [Plotting] Plots saved for '{exp_name}'")
            
        except Exception as e:
            log(ctx, "info", f"  [Plotting] Error generating plots for '{exp_name}': {e}")
            import traceback
            traceback.print_exc()

    log(ctx, "info", f"  [Orchestration] Aesthetics plots saved to {plots_dir}")
