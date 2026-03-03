import sys
import os

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from src.orchestrator.context import OrchestratorDomainContext, OrchestratorGlobalContext, OrchestratorSystemContext

global_ctx = OrchestratorGlobalContext(config_path="sanity")
domain_ctx = OrchestratorDomainContext(sig_total_experiments=1, sig_experiment_active_idx=0)
system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)

ctx = system_ctx.to_dict()
domain = ctx['domain']

print(f"sig_total_experiments: {domain['sig_total_experiments']}")
print(f"sig_experiment_active_idx: {domain['sig_experiment_active_idx']}")

eval_str = "domain['sig_experiment_active_idx'] < domain['sig_total_experiments']"
result = eval(eval_str, {"domain": domain})
print(f"eval result: {result}")
