from dataclasses import dataclass, field
from theus.context import BaseSystemContext, BaseDomainContext, BaseGlobalContext
from theus.engine import TheusEngine

# Setup Correct Context Structure
@dataclass
class WarehouseDomain(BaseDomainContext):
    total_value: int = 0

@dataclass
class WarehouseConfig(BaseGlobalContext):
    max_capacity: int = 1000

@dataclass
class WarehouseContext(BaseSystemContext):
    domain_ctx: WarehouseDomain = field(default_factory=WarehouseDomain)
    global_ctx: WarehouseConfig = field(default_factory=WarehouseConfig)

def test_engine_edit():
    print("--- Testing engine.edit() Mechanism ---")
    
    ctx = WarehouseContext()
    engine = TheusEngine(ctx, strict_mode=True)
    
    # 1. Verify locked state initially
    try:
        ctx.domain_ctx.total_value = 1
        print("❌ FAILED: Initial state should be locked!")
    except Exception:
        print("✅ Correctly locked initially.")

    # 2. Test engine.edit()
    print("Attempting modification inside 'with engine.edit()':")
    try:
        with engine.edit() as safe_ctx:
            # Check identity
            if safe_ctx is not ctx:
                print("⚠️ Warning: safe_ctx is not the same object as ctx (acceptable but worth noting)")
            
            # Modify
            safe_ctx.domain_ctx.total_value = 500
            print(f"   Value set to: {safe_ctx.domain_ctx.total_value}")
            print("✅ Modification inside block SUCCEEDED.")
    except Exception as e:
        print(f"❌ FAILED inside block: {e}")
        return

    # 3. Verify value persists
    if ctx.domain_ctx.total_value == 500:
        print(f"✅ Value persisted: {ctx.domain_ctx.total_value}")
    else:
        print(f"❌ FAILED: Value not persisted, got {ctx.domain_ctx.total_value}")

    # 4. Verify relock
    print("Attempting modification AFTER block:")
    try:
        ctx.domain_ctx.total_value = 999
        print("❌ FAILED: Should be re-locked after block!")
    except Exception as e:
        print(f"✅ PASSED: Modification blocked after exit ({type(e).__name__})")

if __name__ == "__main__":
    test_engine_edit()
