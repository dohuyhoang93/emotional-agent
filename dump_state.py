import asyncio
import os
import sys

# Ensure project root is in path
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from theus.engine import TheusEngine
from src.orchestrator.context import OrchestratorSystemContext, OrchestratorGlobalContext, OrchestratorDomainContext

global_ctx = OrchestratorGlobalContext(config_path="experiments_sanity.json")
domain_ctx = OrchestratorDomainContext()
system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)

engine = TheusEngine(context=system_ctx, strict_guards=False)
engine.scan_and_register("src/orchestrator/processes")

async def test():
    await engine.execute("load_config")
    
    raw = engine._core.state.data
    print("--- RAW STATE KEYS ---")
    for k in raw.keys():
        print(f"Key: {k}")
        
    print("\n--- DOMAIN KEYS ---")
    domain = raw.get("domain", {})
    if isinstance(domain, dict):
        for k, v in domain.items():
            if k.startswith("sig_"):
                print(f"{k}: {v}")
    else:
        print(f"domain is not a dict: {type(domain)}")

asyncio.run(test())
