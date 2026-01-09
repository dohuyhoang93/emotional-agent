import sys
import os

sys.path.append(os.getcwd())
sys.path.append('theus')

try:
    from theus.guards import ContextGuard
    from theus.contracts import ContractViolationError
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

class DummyContext:
    def __init__(self):
        self.val_float = 1.5
        self.val_int = 10
        self.child_ctx = ChildContext()

class ChildContext:
    def __init__(self):
        self.attr = 100

def test():
    print("Testing REAL ContextGuard Primitive Access...")
    d = DummyContext()
    
    # Inputs allow everything for test
    g = ContextGuard(d, allowed_inputs={'val_float', 'val_int', 'child_ctx', 'child_ctx.attr'}, allowed_outputs=set())
    
    print(f"Direct float: {d.val_float}")
    print(f"Guard float: {g.val_float}")
    print(f"Type of Guard float: {type(g.val_float)}")
    
    try:
        f = float(g.val_float)
        print(f"Cast float: {f}")
    except Exception as e:
        print(f"FAILED cast float: {e}")

    print(f"Guard child ctx: {type(g.child_ctx)}") # Should NOT be wrapped unless I named it _ctx
    
    # Test naming convention wrapping
    print("--- Testing _ctx wrapping ---")
    g_child = g.child_ctx
    print(f"Type of g.child_ctx (should be raw unless _ctx logic applies to content? No, only name): {type(g_child)}")
    
    # What if I name it sub_ctx?
    d.sub_ctx = ChildContext()
    g2 = ContextGuard(d, allowed_inputs={'sub_ctx.attr', 'sub_ctx'}, allowed_outputs=set())
    print(f"Type of g2.sub_ctx: {type(g2.sub_ctx)}") 
    
    if hasattr(g2.sub_ctx, '_target_obj'):
        print("YES, sub_ctx IS WRAPPED.")
    else:
        print("NO, sub_ctx is NOT wrapped.")

if __name__ == "__main__":
    test()
