import os
from src.core.engine import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain.final_report', 'domain.output_dir'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def save_summary(ctx: OrchestratorSystemContext):
    """
    Process: Lưu báo cáo tóm tắt cuối cùng vào tệp văn bản.
    """
    log(ctx, "info", "  [Orchestration] Saving final summary report...")
    domain = ctx.domain_ctx

    summary_file_path = os.path.join(domain.output_dir, "summary_report.txt")
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(domain.final_report)
    
    log(ctx, "info", f"  [Orchestration] Final summary report saved to: {summary_file_path}")
