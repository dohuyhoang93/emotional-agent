
import sys
from theus_core import ContextGuard
# We can't easily instantiate RustSystemContext directly if it expects args we don't know, 
# but ContextGuard expects any python object?
# Actually ContextGuard::new_py takes (obj, inputs, outputs, ...)

class MockGlobal:
    pass

class MockDomain:
    def __init__(self):
        self.current_observation = None
        self.previous_observation = None

class MockSystem:
    def __init__(self):
        self.global_ctx = MockGlobal()
        self.domain_ctx = MockDomain()

def test_guard():
    sys_ctx = MockSystem()
    
    # inputs same as p1_perception (Fix 1)
    # inputs=['domain_ctx.current_observation']
    # outputs=['domain_ctx.previous_observation']
    
    inputs = ['domain_ctx.current_observation']
    outputs = ['domain_ctx.previous_observation', 'domain_ctx.current_observation']
    
    print(f"Creating guard with inputs={inputs}, outputs={outputs}")
    
    try:
        # ContextGuard(obj, inputs, outputs) as per guards.rs #[new] fn new_py
        guard = ContextGuard(sys_ctx, inputs, outputs)
        
        print("Guard created.")
        
        # Test Read domain_ctx (access root attr)
        print("Accessing guard.domain_ctx...")
        d_ctx = guard.domain_ctx
        print("Access domain_ctx success.")
        
        # Test Read current_observation
        print("Accessing domain_ctx.current_observation...")
        obs = d_ctx.current_observation
        print("Access current_observation success.")
        
        # Test Write previous_observation
        print("Writing domain_ctx.previous_observation...")
        d_ctx.previous_observation = "new_val"
        print("Write previous_observation success.")
        
    except Exception as e:
        print(f"Caught Exception: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_guard()
