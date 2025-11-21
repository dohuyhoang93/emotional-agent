import pandas as pd
import os
import numpy as np
from src.experiment_context import OrchestrationContext
from src.logger import log, log_error # Import the new logger

def p_analyze_data(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để phân tích dữ liệu tổng hợp và tạo báo cáo tóm tắt.
    Tự động xác định đường đi tối ưu và tính toán thời điểm hội tụ.
    """
    log(context, "info", "  [Orchestration] Analyzing aggregated data...")

    summary_report_lines = ["--- BÁO CÁO TỔNG KẾT THỬ NGHIỆM ---"]
    summary_report_lines.append(f"Thời gian chạy: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_report_lines.append(f"Thư mục kết quả: {context.global_output_dir}\n")

    # --- Bước 1: Tự động xác định đường đi tối ưu trên toàn bộ tập dữ liệu ---
    optimal_path_length = float('inf')
    all_data_exists = any(not exp.aggregated_data.empty for exp in context.experiments)
    
    if all_data_exists:
        all_dfs = [exp.aggregated_data for exp in context.experiments if not exp.aggregated_data.empty]
        full_df = pd.concat(all_dfs, ignore_index=True)
        successful_runs = full_df[full_df['success'] == True]
        if not successful_runs.empty:
            optimal_path_length = successful_runs['steps'].min()

    if optimal_path_length == float('inf'):
        log(context, "info", "CẢNH BÁO: Không tìm thấy bất kỳ episode thành công nào trong tất cả các thử nghiệm. Không thể xác định đường đi tối ưu.")
    else:
        log(context, "info", f"  [Analysis] Đường đi tối ưu được xác định động là: {optimal_path_length} bước.")


    # --- Bước 2: Phân tích từng thử nghiệm và tạo báo cáo ---
    for exp_def in context.experiments:
        summary_report_lines.append(f"=== Thử nghiệm: {exp_def.name} ===")
        summary_report_lines.append(f"  Số lần chạy: {exp_def.runs}")
        summary_report_lines.append(f"  Số episode mỗi lần chạy: {exp_def.episodes_per_run}")
        summary_report_lines.append(f"  Tham số: {exp_def.parameters}")

        if not exp_def.aggregated_data.empty:
            df_agg = exp_def.aggregated_data

            # Tính toán tỷ lệ thành công trung bình
            mean_success_rate = df_agg.groupby('episode')['success'].mean().mean() * 100
            summary_report_lines.append(f"  Tỷ lệ thành công trung bình (tất cả episode): {mean_success_rate:.2f}%")

            # Tính toán số bước trung bình cho các episode thành công
            df_successful = df_agg[df_agg['success'] == True]
            if not df_successful.empty:
                mean_steps_successful = df_successful.groupby('episode')['steps'].mean().mean()
                summary_report_lines.append(f"  Số bước trung bình cho episode thành công: {mean_steps_successful:.2f}")
            else:
                summary_report_lines.append("  Không có episode thành công nào để tính số bước trung bình.")
            
            # Tỷ lệ khám phá cuối cùng trung bình
            mean_final_exploration_rate = df_agg.groupby('episode')['final_exploration_rate'].mean().iloc[-1]
            summary_report_lines.append(f"  Tỷ lệ khám phá cuối cùng trung bình: {mean_final_exploration_rate:.4f}")

            # Phân tích thời điểm tìm ra đường đi tối ưu (nếu đã xác định được)
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
            
        else:
            summary_report_lines.append("  Không có dữ liệu tổng hợp cho thử nghiệm này.")
        summary_report_lines.append("\n")

    context.final_report = "\n".join(summary_report_lines)
    log(context, "info", "  [Orchestration] Analysis complete.")
    return context
