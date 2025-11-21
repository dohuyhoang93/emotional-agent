import os
from src.experiment_context import OrchestrationContext
from src.logger import log, log_error # Import the new logger

def p_save_summary(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để lưu báo cáo tóm tắt cuối cùng vào một tệp văn bản.
    """
    log(context, "info", "  [Orchestration] Saving final summary report...")

    summary_file_path = os.path.join(context.global_output_dir, "summary_report.txt")
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(context.final_report)
    
    log(context, "info", f"  [Orchestration] Final summary report saved to: {summary_file_path}")
    return context
