from src.experiment_context import OrchestrationContext
import pandas as pd

def p_analyze_data(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để phân tích dữ liệu tổng hợp và tạo báo cáo tóm tắt.
    """
    print("  [Orchestration] Analyzing aggregated data...")

    summary_report_lines = ["--- BÁO CÁO TỔNG KẾT THỬ NGHIỆM ---"]
    summary_report_lines.append(f"Thời gian chạy: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_report_lines.append(f"Thư mục kết quả: {context.global_output_dir}\n")

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

            # Có thể thêm các phân tích thống kê khác ở đây (ví dụ: độ lệch chuẩn, khoảng tin cậy) 
            
        else:
            summary_report_lines.append("  Không có dữ liệu tổng hợp cho thử nghiệm này.")
        summary_report_lines.append("\n")

    context.final_report = "\n".join(summary_report_lines)
    print("  [Orchestration] Analysis complete.")
    return context
