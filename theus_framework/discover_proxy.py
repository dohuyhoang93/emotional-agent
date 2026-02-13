from theus.engine import TheusEngine
import asyncio

async def test():
    engine = TheusEngine()
    # Create some list data
    engine.compare_and_swap(0, data={"domain": {"log": ["a", "b"]}})
    
    async def proc_1(ctx):
        log_proxy = ctx.domain.log
        print(f"DEBUG: log_proxy type: {type(log_proxy)}")
        print(f"DEBUG: log_proxy._inner type: {type(log_proxy._inner)}")
        print(f"DEBUG: log_proxy._inner dir: {dir(log_proxy._inner)}")
        
        # Try to read capabilities
        for attr in ["capabilities", "_capabilities", "caps", "cap"]:
             if hasattr(log_proxy._inner, attr):
                  print(f"DEBUG: Found {attr}: {getattr(log_proxy._inner, attr)}")
        return "ok"
    
    await engine.execute(proc_1)

if __name__ == "__main__":
    asyncio.run(test())
