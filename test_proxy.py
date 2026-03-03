import asyncio
from theus.contracts import process
from theus.engine import TheusEngine
from src.orchestrator.context import OrchestratorSystemContext, OrchestratorGlobalContext, OrchestratorDomainContext

global_ctx = OrchestratorGlobalContext()
domain_ctx = OrchestratorDomainContext()
system_ctx = OrchestratorSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)

engine = TheusEngine(context=system_ctx, strict_guards=False)

@process(inputs=["domain"], outputs=[], side_effects=[], errors=[])
def simple_process(ctx):
    print("CTX TYPE:", type(ctx))
    print("DIR CTX:", dir(ctx))
    
    # Check if we can get the inner object somehow
    print("get_attr:", ctx._inner if hasattr(ctx, "_inner") else "No _inner")
    print("get_attr:", ctx.target if hasattr(ctx, "target") else "No target")
    print("get_attr:", ctx.inner if hasattr(ctx, "inner") else "No inner")
    
    return {}

engine._core.register_process("simple_process", simple_process)

async def test():
    await engine.execute("simple_process")

asyncio.run(test())
