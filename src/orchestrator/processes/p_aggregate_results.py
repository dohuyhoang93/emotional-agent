import pandas as pd
import os
from src.core.engine import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log, log_error

@process(
    inputs=['domain.experiments', 'log_level'],
    outputs=['domain.experiments'],
    side_effects=['filesystem.read'],
    errors=['pandas.read_error']
)
def aggregate_results(ctx: OrchestratorSystemContext):
    """
    Process: Tổng hợp kết quả từ các lần chạy riêng lẻ.
    """
    log(ctx, "info", "  [Orchestration] Aggregating results...")
    domain = ctx.domain_ctx

    for exp_def in domain.experiments:
        log(ctx, "info", f"    [Experiment: {exp_def.name}] Aggregating data...")
        
        all_runs_data = []
        for exp_run in exp_def.list_of_runs:
            if exp_run.status == "COMPLETED" and os.path.exists(exp_run.output_csv_path):
                try:
                    df_run = pd.read_csv(exp_run.output_csv_path)
                    df_run['run_id'] = exp_run.run_id # Add Run ID
                    all_runs_data.append(df_run)
                except Exception as e:
                    log_error(ctx, f"Không thể đọc tệp CSV '{exp_run.output_csv_path}': {e}")
            elif exp_run.status == "FAILED":
                log(ctx, "info", f"CẢNH BÁO: Run {exp_run.run_id} của thử nghiệm '{exp_def.name}' thất bại, bỏ qua.")
            else:
                log(ctx, "info", f"CẢNH BÁO: Tệp CSV '{exp_run.output_csv_path}' không tồn tại hoặc run chưa hoàn thành, bỏ qua.")
        
        if all_runs_data:
            exp_def.aggregated_data = pd.concat(all_runs_data, ignore_index=True)
            log(ctx, "info", f"    [Experiment: {exp_def.name}] Aggregated data for {len(all_runs_data)} successful runs.")
        else:
            log(context=ctx, message_level="info", message=f"    [Experiment: {exp_def.name}] Không có dữ liệu để tổng hợp.")
            exp_def.aggregated_data = pd.DataFrame() 

    log(ctx, "info", "  [Orchestration] Aggregation complete.")
