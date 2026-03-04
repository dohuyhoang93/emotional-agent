"""
Context Helpers for v2/v3 Compatibility.

Theus v3 wraps Python dataclass contexts into Rust State, which presents
domain context as a dict instead of the original object. These helpers
provide a unified way to access context attributes regardless of type.
"""
from typing import Any, Tuple


def get_domain_ctx(ctx) -> Tuple[Any, bool]:
    """
    Extract domain context from ContextGuard.
    Returns: Tuple of (domain_context, is_dict)
    
    NOTE: Prioritizes _inner._target path to avoid triggering COW deepcopy
    which causes RuntimeWarning when Transaction objects are in the data graph.
    """
    import warnings

    # Priority 1: Direct access via ContextGuard internals (no COW)
    if hasattr(ctx, '_inner'):
        try:
            target = getattr(ctx._inner, '_target', None)
            if target:
                if hasattr(target, 'domain_ctx') and getattr(target, 'domain_ctx') is not None:
                    return getattr(target, 'domain_ctx'), isinstance(getattr(target, 'domain_ctx'), dict)
                if hasattr(target, 'domain') and getattr(target, 'domain') is not None:
                    return getattr(target, 'domain'), isinstance(getattr(target, 'domain'), dict)
        except Exception:
            pass

    # Priority 2: Standard python dataclass
    try:
        if hasattr(ctx, 'domain_ctx') and ctx.domain_ctx is not None:
            return ctx.domain_ctx, isinstance(ctx.domain_ctx, dict)
    except PermissionError:
        pass
        
    try:
        if hasattr(ctx, 'domain') and ctx.domain is not None:
            return ctx.domain, isinstance(ctx.domain, dict)
    except PermissionError:
        pass

    # Priority 3: Dict-like access (may trigger COW — suppress warnings)
    if hasattr(ctx, '__getitem__'):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            try:
                domain = ctx['domain']
                if domain is not None:
                    return domain, True
            except (KeyError, PermissionError, RuntimeError):
                pass
                
            try:
                domain_ctx = ctx['domain_ctx']
                if domain_ctx is not None:
                    return domain_ctx, True
            except (KeyError, PermissionError, RuntimeError):
                pass

    raise ValueError(f"CRITICAL: Cannot extract domain context from {type(ctx)}.")


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
    if hasattr(obj, '_inner') or hasattr(obj, 'is_proxy'):
        # ContextGuard or SupervisorProxy should be accessed via getattr
        return getattr(obj, key, default)
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
    Extract global context from ContextGuard
    Returns: Tuple of (global_context, is_dict)
    """
    if hasattr(ctx, '__getitem__'):
        try:
            global_ctx = ctx['global']
            if global_ctx is not None:
                return global_ctx, True
        except (KeyError, PermissionError):
            pass
            
        try:
            global_ctx_prop = ctx['global_ctx']
            if global_ctx_prop is not None:
                return global_ctx_prop, True
        except (KeyError, PermissionError):
            pass

    if hasattr(ctx, '_inner'):
        # We are inside a ContextGuard
        try:
            target = getattr(ctx._inner, '_target', None)
            if target:
                if hasattr(target, 'global_ctx') and getattr(target, 'global_ctx') is not None:
                    return getattr(target, 'global_ctx'), isinstance(getattr(target, 'global_ctx'), dict)
                if hasattr(target, 'global') and getattr(target, 'global') is not None:
                    return getattr(target, 'global'), isinstance(getattr(target, 'global'), dict)
        except Exception:
            pass

    # Standard python dataclass
    try:
        if hasattr(ctx, 'global_ctx') and getattr(ctx, 'global_ctx') is not None:
            return getattr(ctx, 'global_ctx'), isinstance(getattr(ctx, 'global_ctx'), dict)
    except PermissionError:
        pass
        
    try:
        if hasattr(ctx, 'global') and getattr(ctx, 'global') is not None:
            return getattr(ctx, 'global'), isinstance(getattr(ctx, 'global'), dict)
    except PermissionError:
        pass

    raise ValueError(f"CRITICAL: Cannot extract global context from {type(ctx)}.")
