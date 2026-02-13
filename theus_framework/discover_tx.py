from theus.engine import TheusEngine
import asyncio

async def test():
    engine = TheusEngine(context={"domain": {"log_history": ["a"]}})
    
    async def proc(ctx):
        from theus.contracts import AdminTransaction
        with AdminTransaction(ctx) as admin:
            guard = admin.domain.log_history
            print(f"DEBUG: guard.transaction: {guard.transaction}")
            print(f"DEBUG: guard.transaction type: {type(guard.transaction)}")
            print(f"DEBUG: guard.transaction dir: {dir(guard.transaction)}")
        return "ok"
    
    await engine.execute(proc)

if __name__ == "__main__":
    asyncio.run(test())
