"""
Context Helpers for v2/v3 Compatibility.

Theus v3 wraps Python dataclass contexts into Rust State, which presents
domain context as a dict instead of the original object. These helpers
provide a unified way to access context attributes regardless of type.
"""
from typing import Any, Tuple


def get_domain_ctx(ctx) -> Tuple[Any, bool]:
    """
    Extract domain context from either:
    - Python OrchestratorSystemContext (ctx.domain_ctx -> object)
    - Rust State (ctx.state.data["domain"] -> dict)
    
    Returns:
        Tuple of (domain_context, is_dict)
    """
    # Try Python dataclass style first (preferred)
    # Check if it has 'experiments' attribute to confirm it's the Object, not a Dict
    if hasattr(ctx, 'domain_ctx') and hasattr(ctx.domain_ctx, 'experiments'):
        return ctx.domain_ctx, False
    
    # Try Rust State style
    if hasattr(ctx, 'state') and hasattr(ctx.state, 'data'):
        data = ctx.state.data
        domain = data.get('domain') if hasattr(data, 'get') else getattr(data, 'domain', None)
        if domain is not None:
            return domain, isinstance(domain, dict)
    
    # Fallback: ctx.domain_ctx exists but might be a dict (if modified by Engine)
    if hasattr(ctx, 'domain_ctx'):
        d = ctx.domain_ctx
        return d, isinstance(d, dict)
    
    raise AttributeError(f"Cannot extract domain context from {type(ctx)}")


def get_attr(obj: Any, key: str, default: Any = None) -> Any:
    """
    Get attribute from either dict or object.
    
    Args:
        obj: Either a dict or an object with attributes
        key: The attribute/key name
        default: Default value if not found
    
    Returns:
        The value or default
    """
    if isinstance(obj, dict):
        return obj.get(key, default)
    else:
        return getattr(obj, key, default)


def set_attr(obj: Any, key: str, value: Any) -> None:
    """
    Set attribute on either dict or object.
    
    Args:
        obj: Either a dict or an object with attributes
        key: The attribute/key name
        value: The value to set
    """
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def get_global_ctx(ctx) -> Tuple[Any, bool]:
    """
    Extract global context from either:
    - Python OrchestratorSystemContext (ctx.global_ctx -> object)
    - Rust State (ctx.state.data["global"] -> dict)
    
    Returns:
        Tuple of (global_context, is_dict)
    """
    # Try Python dataclass style first
    if hasattr(ctx, 'global_ctx') and hasattr(ctx.global_ctx, 'config_path'):
        return ctx.global_ctx, False
    
    # Try Rust State style
    if hasattr(ctx, 'state') and hasattr(ctx.state, 'data'):
        data = ctx.state.data
        global_ctx = data.get('global') if hasattr(data, 'get') else getattr(data, 'global', None)
        if global_ctx is not None:
            return global_ctx, isinstance(global_ctx, dict)
    
    # Fallback
    if hasattr(ctx, 'global_ctx'):
        d = ctx.global_ctx
        return d, isinstance(d, dict)
    
    raise AttributeError(f"Cannot extract global context from {type(ctx)}")
