from theus.engine import TheusEngine
import asyncio

async def test():
    engine = TheusEngine(context={"domain": {"log": ["a", "b"]}})
    
    # Reach into core directly to get a native proxy
    log_proxy = engine._core.state.data["domain"]["log"]
         
    print(f"DEBUG: log_proxy type: {type(log_proxy)}")
    print(f"DEBUG: log_proxy dir: {dir(log_proxy)}")
    
    for attr in ["capabilities", "_capabilities", "caps", "cap", "is_admin"]:
         if hasattr(log_proxy, attr):
              print(f"DEBUG: Found {attr}: {getattr(log_proxy, attr)}")

if __name__ == "__main__":
    asyncio.run(test())
