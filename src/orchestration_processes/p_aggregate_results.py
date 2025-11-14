import pandas as pd
import os
from src.experiment_context import OrchestrationContext

def p_aggregate_results(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để tổng hợp kết quả từ các lần chạy riêng lẻ của mỗi thử nghiệm.
    """
    print("  [Orchestration] Aggregating results...")

    for exp_def in context.experiments:
        print(f"    [Experiment: {exp_def.name}] Aggregating data...")
        
        all_runs_data = []
        for exp_run in exp_def.list_of_runs:
            if exp_run.status == "COMPLETED" and os.path.exists(exp_run.output_csv_path):
                try:
                    df_run = pd.read_csv(exp_run.output_csv_path)
                    df_run['run_id'] = exp_run.run_id # Thêm cột run_id để phân biệt các lần chạy
                    all_runs_data.append(df_run)
                except Exception as e:
                    print(f"LỖI: Không thể đọc tệp CSV '{exp_run.output_csv_path}': {e}")
            elif exp_run.status == "FAILED":
                print(f"CẢNH BÁO: Run {exp_run.run_id} của thử nghiệm '{exp_def.name}' thất bại, bỏ qua.")
            else:
                print(f"CẢNH BÁO: Tệp CSV '{exp_run.output_csv_path}' không tồn tại hoặc run chưa hoàn thành, bỏ qua.")
        
        if all_runs_data:
            exp_def.aggregated_data = pd.concat(all_runs_data, ignore_index=True)
            print(f"    [Experiment: {exp_def.name}] Aggregated data for {len(all_runs_data)} successful runs.")
        else:
            print(f"    [Experiment: {exp_def.name}] Không có dữ liệu để tổng hợp.")
            exp_def.aggregated_data = pd.DataFrame() # Đảm bảo là một DataFrame rỗng

    print("  [Orchestration] Aggregation complete.")
    return context
