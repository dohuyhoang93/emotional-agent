import os
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log

@process(
    inputs=['domain_ctx', 'domain', 'domain.final_report', 'domain.output_dir', 'log_level'],
    outputs=[],
    side_effects=['filesystem.write'],
    errors=[]
)
def save_summary(ctx: OrchestratorSystemContext):
    """
    Process: Lưu báo cáo tóm tắt cuối cùng vào tệp văn bản.
    """
    log(ctx, "info", "  [Orchestration] Saving final summary report...")

    output_dir = getattr(ctx.domain, 'output_dir', 'results')
    final_report = getattr(ctx.domain, 'final_report', 'No report generated.')
    
    summary_file_path = os.path.join(output_dir, "summary_report.txt")
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(str(final_report))
    
    log(ctx, "info", f"  [Orchestration] Final summary report saved to: {summary_file_path}")
    return {}
