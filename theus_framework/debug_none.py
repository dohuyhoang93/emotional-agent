import asyncio
import theus.context
print("CONTEXT MODULE PATH:", theus.context.__file__)
from theus.engine import TheusEngine
from theus.contracts import process
from theus.contracts import process

engine = TheusEngine(context={"domain": {}})

@process(inputs=["domain"], outputs=["domain"])
async def fast_process(ctx):
    print("INSIDE PROCESS!")
    print("CTX TYPE:", type(ctx))
    print("CTX._target:", getattr(ctx, "_target", "NOT_FOUND"))
    print("CTX._inner:", getattr(ctx, "_inner", "NOT_FOUND"))
    
    domain_val = ctx.domain
    print("CTX.DOMAIN IS:", domain_val)
    print("CTX.DOMAIN TYPE:", type(domain_val))
    
    ctx.domain.counter = 2
    print("SUCCESSFULLY SET COUNTER!")

async def main():
    print("ENGINE STATE VERSION:", engine.state.version)
    
    # Try fetching domain proxy natively from State
    try:
        data_dict = engine.state.data
        print("STATE.DATA TYPE:", type(data_dict))
        print("STATE.DATA DOMAIN KEY:", data_dict.get("domain", "MISSING"))
    except Exception as e:
        print("ERROR NATIVE DATA:", e)

    # Execute
    try:
        await engine.execute(fast_process)
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
