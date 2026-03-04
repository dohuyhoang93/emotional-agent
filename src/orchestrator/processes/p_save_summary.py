import os
from theus.contracts import process
from src.orchestrator.context import OrchestratorSystemContext
from src.orchestrator.context_helpers import get_domain_ctx, get_attr
from src.logger import log

@process(
    inputs=['domain_ctx', 'domain', 'domain.final_report', 'domain.output_dir', 'log_level'],
    outputs=['domain_ctx', ],
    side_effects=['filesystem.write'],
    errors=[]
)
def save_summary(ctx: OrchestratorSystemContext):
    """
    Process: Lưu báo cáo tóm tắt cuối cùng vào tệp văn bản.
    """
    log(ctx, "info", "  [Orchestration] Saving final summary report...")
    domain, is_dict = get_domain_ctx(ctx)

    output_dir = get_attr(domain, 'output_dir', 'results')
    final_report = get_attr(domain, 'final_report', 'No report generated.')
    
    summary_file_path = os.path.join(output_dir, "summary_report.txt")
    with open(summary_file_path, "w", encoding="utf-8") as f:
        f.write(str(final_report))
    
    log(ctx, "info", f"  [Orchestration] Final summary report saved to: {summary_file_path}")
    return {}

