try:
    from theus_core import ContextGuard
except ImportError:
    print("Failed to import ContextGuard from theus_core")
    exit(1)

import inspect

print("Checking ContextGuard...")
print(f"Has __getitem__: {'__getitem__' in dir(ContextGuard)}")
print(f"Has __setitem__: {'__setitem__' in dir(ContextGuard)}")
print(f"Start of dir: {dir(ContextGuard)[:10]}")
