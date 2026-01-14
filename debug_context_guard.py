
import sys
try:
    from theus_core import ContextGuard
    print(f"ContextGuard: {ContextGuard}")
    print(f"Module: {ContextGuard.__module__}")
    print(f"Name: {ContextGuard.__name__}")
    print(f"Bases: {ContextGuard.__bases__}")
    
    # Try subclassing
    class MyGuard(ContextGuard):
        pass
    print("Subclassing successful!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
