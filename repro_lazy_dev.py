from theus import TheusEngine, process
from theus import BaseGlobalContext, BaseDomainContext, BaseSystemContext
from dataclasses import dataclass, field

@dataclass
class MyDomain(BaseDomainContext):
    secret_data: str = "hidden"
    public_data: str = "visible"

@dataclass
class MySystem(BaseSystemContext):
    pass

# The "Lazy" Process - Requesting the entire domain root
@process(
    inputs=['domain'], 
    outputs=['domain'],
    side_effects=[],
    errors=[]
)
def lazy_process(ctx: MySystem):
    # Accessing deep nested data without declaring it explicitly
    print(f"Reading secret: {ctx.domain_ctx.secret_data}")
    
    # Modifying data without explicit path declaration
    ctx.domain_ctx.secret_data = "EXPOSED"
    return "Success"

def test_exploit():
    dom = MyDomain()
    sys_ctx = MySystem(global_ctx=BaseGlobalContext(), domain_ctx=dom)
    
    engine = TheusEngine(sys_ctx, strict_mode=True) # Strict mode is ON
    engine.register_process("lazy", lazy_process)
    
    print("--- Attempting Exploit ---")
    try:
        engine.run_process("lazy")
        print(f"Post-Process State: {dom.secret_data}")
        if dom.secret_data == "EXPOSED":
            print("✅ VULNERABILITY CONFIRMED: Granular checks bypassed via root access.")
    except Exception as e:
        print(f"❌ BLOCKED: {e}")

if __name__ == "__main__":
    test_exploit()
