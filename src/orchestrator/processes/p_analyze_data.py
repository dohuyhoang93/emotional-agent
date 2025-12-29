import numpy as np
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain.experiments', 'domain.output_dir', 'log_level'],
    outputs=['domain.final_report'],
    side_effects=[],
    errors=[]
)
def analyze_data(ctx: OrchestratorSystemContext):
    """
    Process: Analyze aggregated multi-agent experiment data.
    
    NOTE: Updated to handle JSON metrics format (no 'success' column).
    """
    log(ctx, "info", "  [Orchestration] Analyzing aggregated data...")
    domain = ctx.domain_ctx

    summary_report_lines = ["--- MULTI-AGENT EXPERIMENT SUMMARY ---"]
    summary_report_lines.append(f"Output directory: {domain.output_dir}\n")

    for exp_def in domain.experiments:
        summary_report_lines.append(f"=== Experiment: {exp_def.name} ===")
        summary_report_lines.append(f"  Runs: {exp_def.runs}")
        summary_report_lines.append(f"  Episodes per run: {exp_def.episodes_per_run}")
        summary_report_lines.append(f"  Parameters: {exp_def.parameters}\n")

        if exp_def.aggregated_data:
            metrics = exp_def.aggregated_data
            
            # Extract key metrics
            episodes = [m.get('episode', 0) for m in metrics]
            avg_rewards = [m.get('avg_reward', 0.0) for m in metrics]
            best_rewards = [m.get('best_reward', 0.0) for m in metrics]
            
            # Social learning metrics
            social_transfers = [m.get('social_learning_transfers', 0) for m in metrics]
            total_synapses = [m.get('social_learning_synapses', 0) for m in metrics]
            
            # Revolution metrics
            revolutions = [m.get('revolutions', 0) for m in metrics]
            
            # Overall statistics
            total_episodes = len(metrics)
            final_avg_reward = avg_rewards[-1] if avg_rewards else 0.0
            best_overall_reward = max(best_rewards) if best_rewards else 0.0
            
            # Success Rate metrics
            success_rates = [m.get('success_rate', 0.0) for m in metrics]
            final_success_rate = np.mean(success_rates[-10:]) if len(success_rates) >= 10 else (success_rates[-1] if success_rates else 0.0)
            
            summary_report_lines.append(f"  Total Episodes: {total_episodes}")
            summary_report_lines.append(f"  Final Avg Reward: {final_avg_reward:.4f}")
            summary_report_lines.append(f"  Best Reward Achieved: {best_overall_reward:.4f}")
            summary_report_lines.append(f"  Final Success Rate: {final_success_rate*100:.2f}%")
            
            # Social learning summary
            total_transfers = sum(social_transfers)
            total_synapses_transferred = sum(total_synapses)
            summary_report_lines.append(f"\n  Social Learning:")
            summary_report_lines.append(f"    Total Transfers: {total_transfers}")
            summary_report_lines.append(f"    Total Synapses: {total_synapses_transferred}")
            
            # Revolution summary
            total_revolutions = sum(revolutions)
            summary_report_lines.append(f"\n  Revolution Protocol:")
            summary_report_lines.append(f"    Total Revolutions: {total_revolutions}")
            
            # Learning progress (last 10% of episodes)
            last_10_percent = int(total_episodes * 0.1)
            if last_10_percent > 0:
                final_phase_rewards = avg_rewards[-last_10_percent:]
                final_phase_avg = np.mean(final_phase_rewards) if final_phase_rewards else 0.0
                final_phase_success = np.mean(success_rates[-last_10_percent:]) if success_rates else 0.0
                summary_report_lines.append(f"\n  Final Phase (last 10% episodes):")
                summary_report_lines.append(f"    Avg Reward: {final_phase_avg:.4f}")
                summary_report_lines.append(f"    Success Rate: {final_phase_success*100:.2f}%")
            
            # Trend analysis (every 10% of episodes)
            chunk_size = max(1, total_episodes // 10)
            summary_report_lines.append(f"\n  Learning Trend (every 10%):")
            for i in range(0, total_episodes, chunk_size):
                chunk_rewards = avg_rewards[i:i+chunk_size]
                chunk_success = success_rates[i:i+chunk_size]
                if chunk_rewards:
                    chunk_avg = np.mean(chunk_rewards)
                    chunk_succ_avg = np.mean(chunk_success)
                    summary_report_lines.append(f"    Episodes {i}-{min(i+chunk_size, total_episodes)}: Reward={chunk_avg:.2f}, Success={chunk_succ_avg*100:.1f}%")

        else:
            summary_report_lines.append("  No aggregated data for this experiment.")
        
        summary_report_lines.append("\n")

    domain.final_report = "\n".join(summary_report_lines)
    log(ctx, "info", "  [Orchestration] Analysis complete.")
