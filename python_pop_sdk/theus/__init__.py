# Theus Wrapper Package
# This allows 'python -m theus' execution while keeping 'pop' module structure.

try:
    from pop import *
except ImportError:
    pass
