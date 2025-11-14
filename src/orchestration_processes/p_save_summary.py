import os
from src.experiment_context import OrchestrationContext

def p_save_summary(context: OrchestrationContext) -> OrchestrationContext:
    """
    Process để lưu báo cáo tóm tắt cuối cùng vào một tệp văn bản.
    """
    print("  [Orchestration] Saving final summary report...")

    summary_file_path = os.path.join(context.global_output_dir, "summary_report.txt")
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(context.final_report)
    
    print(f"  [Orchestration] Final summary report saved to: {summary_file_path}")
    return context
