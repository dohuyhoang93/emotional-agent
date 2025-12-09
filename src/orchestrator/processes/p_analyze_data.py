import pandas as pd
import numpy as np
from src.core.engine import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain.experiments', 'domain.output_dir'],
    outputs=['domain.final_report'],
    side_effects=[],
    errors=[]
)
def analyze_data(ctx: OrchestratorSystemContext):
    """
    Process: Phân tích dữ liệu tổng hợp và tạo báo cáo tóm tắt.
    """
    log(ctx, "info", "  [Orchestration] Analyzing aggregated data...")
    domain = ctx.domain_ctx

    summary_report_lines = ["--- BÁO CÁO TỔNG KẾT THỬ NGHIỆM ---"]
    summary_report_lines.append(f"Thời gian chạy: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_report_lines.append(f"Thư mục kết quả: {domain.output_dir}\n")

    # --- Bước 1: Tự động xác định đường đi tối ưu ---
    optimal_path_length = float('inf')
    all_data_exists = any(not exp.aggregated_data.empty for exp in domain.experiments)
    
    if all_data_exists:
        all_dfs = [exp.aggregated_data for exp in domain.experiments if not exp.aggregated_data.empty]
        full_df = pd.concat(all_dfs, ignore_index=True)
        successful_runs = full_df[full_df['success'] == True]
        if not successful_runs.empty:
            optimal_path_length = successful_runs['steps'].min()

    if optimal_path_length == float('inf'):
        log(ctx, "info", "CẢNH BÁO: Không tìm thấy bất kỳ episode thành công nào. Không thể xác định đường đi tối ưu.")
    else:
        log(ctx, "info", f"  [Analysis] Đường đi tối ưu xác định: {optimal_path_length} bước.")

    # --- Bước 2: Phân tích từng thử nghiệm ---
    for exp_def in domain.experiments:
        summary_report_lines.append(f"=== Thử nghiệm: {exp_def.name} ===")
        summary_report_lines.append(f"  Số lần chạy: {exp_def.runs}")
        summary_report_lines.append(f"  Số episode mỗi lần chạy: {exp_def.episodes_per_run}")
        summary_report_lines.append(f"  Tham số: {exp_def.parameters}")

        if not exp_def.aggregated_data.empty:
            df_agg = exp_def.aggregated_data
            mean_success_rate = df_agg.groupby('episode')['success'].mean().mean() * 100
            summary_report_lines.append(f"  Tỷ lệ thành công trung bình (tất cả episode): {mean_success_rate:.2f}%")

            df_successful = df_agg[df_agg['success'] == True]
            if not df_successful.empty:
                mean_steps_successful = df_successful.groupby('episode')['steps'].mean().mean()
                summary_report_lines.append(f"  Số bước trung bình cho episode thành công: {mean_steps_successful:.2f}")
            else:
                summary_report_lines.append("  Không có episode thành công nào để tính số bước trung bình.")
            
            mean_final_exploration_rate = df_agg.groupby('episode')['final_exploration_rate'].mean().iloc[-1]
            summary_report_lines.append(f"  Tỷ lệ khám phá cuối cùng trung bình: {mean_final_exploration_rate:.4f}")

            if optimal_path_length != float('inf'):
                convergence_episodes = []
                for run_id in df_agg['run_id'].unique():
                    run_df = df_agg[df_agg['run_id'] == run_id]
                    optimal_runs = run_df[(run_df['success'] == True) & (run_df['steps'] == optimal_path_length)]
                    if not optimal_runs.empty:
                        first_occurrence_episode = optimal_runs['episode'].min()
                        convergence_episodes.append(first_occurrence_episode)
                    else:
                        convergence_episodes.append(np.nan)
                
                if convergence_episodes:
                    average_convergence_episode = np.nanmean(convergence_episodes)
                    summary_report_lines.append(f"  Episode trung bình tìm ra đường tối ưu ({int(optimal_path_length)} bước): {average_convergence_episode:.2f}")
                else:
                    summary_report_lines.append(f"  Đường tối ưu ({int(optimal_path_length)} bước) không được tìm thấy.")

            # Trend Analysis
            summary_report_lines.append("\n  --- Phân tích Xu hướng (Mỗi 1000 Episodes) ---")
            chunk_size = 1000
            max_episode = df_agg['episode'].max()
            
            for start_ep in range(0, int(max_episode), chunk_size):
                end_ep = min(start_ep + chunk_size, int(max_episode) + 1)
                chunk = df_agg[(df_agg['episode'] >= start_ep) & (df_agg['episode'] < end_ep)]
                
                if not chunk.empty:
                    chunk_success = chunk['success'].mean() * 100
                    chunk_steps = chunk[chunk['success'] == True]['steps'].mean()
                    chunk_reward = chunk['total_reward'].mean()
                    chunk_exploration = chunk['final_exploration_rate'].mean()

                    summary_report_lines.append(f"  Episodes {start_ep}-{end_ep}:")
                    summary_report_lines.append(f"    Success Rate: {chunk_success:.2f}%")
                    summary_report_lines.append(f"    Avg Steps: {chunk_steps:.2f}")
                    summary_report_lines.append(f"    Avg Reward: {chunk_reward:.2f}")
                    summary_report_lines.append(f"    Avg Exploration: {chunk_exploration:.4f}")

            # Finisher Phase
            finisher_start = int(max_episode * 0.9)
            finisher_chunk = df_agg[df_agg['episode'] >= finisher_start]
            if not finisher_chunk.empty:
                finisher_success = finisher_chunk['success'].mean() * 100
                finisher_steps = finisher_chunk[finisher_chunk['success'] == True]['steps'].mean()
                finisher_exploration = finisher_chunk['final_exploration_rate'].mean()

                summary_report_lines.append(f"\n  --- Giai đoạn Về đích (Episodes {finisher_start}-{int(max_episode)}) ---")
                summary_report_lines.append(f"    Success Rate: {finisher_success:.2f}%")
                summary_report_lines.append(f"    Avg Steps: {finisher_steps:.2f}")
                summary_report_lines.append(f"    Avg Exploration: {finisher_exploration:.4f}")

        else:
            summary_report_lines.append("  Không có dữ liệu tổng hợp cho thử nghiệm này.")
        summary_report_lines.append("\n")

    domain.final_report = "\n".join(summary_report_lines)
    log(ctx, "info", "  [Orchestration] Analysis complete.")
