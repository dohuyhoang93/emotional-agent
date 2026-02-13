from theus.engine import TheusEngine
import asyncio

async def test():
    engine = TheusEngine()
    async def proc_1(ctx):
        print(f"DEBUG: ctx type: {type(ctx)}")
        print(f"DEBUG: ctx._inner type: {type(ctx._inner)}")
        print(f"DEBUG: ctx._inner dir: {dir(ctx._inner)}")
        return "ok"
    
    await engine.execute(proc_1)

if __name__ == "__main__":
    asyncio.run(test())
