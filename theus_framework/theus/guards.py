import logging
from typing import Any, Dict, List, Optional, Set, Union
import functools

try:
    import theus_core
    # Handle both maturin develop and installed structures
    if not hasattr(theus_core, "ContextGuard"):
        try:
             from theus_core import theus_core as _core_impl
             _RustContextGuard = _core_impl.ContextGuard
        except ImportError:
             # Fallback if binary is completely missing (should not happen in dev)
             _RustContextGuard = object
    else:
        _RustContextGuard = theus_core.ContextGuard
except ImportError:
    _RustContextGuard = object

class ContextGuard:
    """
    Python wrapper for the Rust ContextGuard (v3.2 RFC-001).
    Provides a cleaner Python API while delegating security to the Rust Core.
    """

    def __init__(
        self,
        target_obj: Any,
        allowed_inputs: Optional[Set[str]] = None,
        allowed_outputs: Optional[Set[str]] = None,
        path_prefix: str = "",
        transaction: Any = None,
        strict_guards: bool = True,
        process_name: str = "Unknown",
        _inner: Any = None,
        parent: Any = None,
        name: Any = None,
        **kwargs
    ):
        self.log = logging.getLogger("theus.guards")
        self.log.extra = {"process_name": process_name}
        
        # [v3.3 Compatibility] Allow 'path' as alias for 'path_prefix'
        if not path_prefix and "path" in kwargs:
             path_prefix = kwargs["path"]
        
        # [v3.3 Compatibility] Manual SupervisorProxy defaults to permissive access
        # Distinguish between None (Manual/Legacy) and set() (Strict Process Contract)
        if allowed_inputs is None:
             from .context import NamespaceRegistry
             allowed_inputs = set(NamespaceRegistry()._namespaces.keys())
             if not allowed_inputs: allowed_inputs = {"default", "domain", "global", "*"}
             
        if allowed_outputs is None and not kwargs.get("read_only", False):
             from .context import NamespaceRegistry
             allowed_outputs = set(NamespaceRegistry()._namespaces.keys())
             if not allowed_outputs: allowed_outputs = {"default", "domain", "global", "*"}
        elif allowed_outputs is None:
             allowed_outputs = set()
             
        # Normalize to sets for Rust Core
        allowed_inputs = set(allowed_inputs) if allowed_inputs is not None else set()
        allowed_outputs = set(allowed_outputs) if allowed_outputs is not None else set()
        
        # [v3.3 Compatibility] Handle 'read_only' flag
        if "read_only" in kwargs and kwargs["read_only"]:
             allowed_outputs = set()
        
        # We track admin status LOCALLY to avoid Illegal Read recursion in Rust
        object.__setattr__(self, "_local_is_admin", False)
        object.__setattr__(self, "path_prefix", path_prefix)
        object.__setattr__(self, "allowed_inputs", allowed_inputs)
        object.__setattr__(self, "allowed_outputs", allowed_outputs)
        object.__setattr__(self, "transaction", transaction)
        object.__setattr__(self, "strict_guards", strict_guards)
        object.__setattr__(self, "parent", parent)
        object.__setattr__(self, "name", name)

        if _inner:
            self._inner = _inner
        else:
            # [RFC-002] Namespace Policy Pre-filtering
            # We filter the allowed lists based on Namespace Registry rules
            from .context import NamespaceRegistry
            registry = NamespaceRegistry()
            
            final_inputs = []
            for path in allowed_inputs:
                ns_name, _ = registry.resolve_path(path)
                policy = registry.get_policy(ns_name)
                if policy.allow_read:
                    final_inputs.append(path)
                else:
                    self.log.warning(f"Process '{process_name}' requested READ to Namespace '{ns_name}' but it is restricted by policy.")

            final_outputs = []
            for path in allowed_outputs:
                ns_name, _ = registry.resolve_path(path)
                policy = registry.get_policy(ns_name)
                if policy.allow_update or policy.allow_append or policy.allow_delete:
                    final_outputs.append(path)
                else:
                    self.log.warning(f"Process '{process_name}' requested WRITE to Namespace '{ns_name}' but it is restricted by policy.")
            
            # [Fix v3.1.2] Update instance whitelists to the filtered versions
            # This ensures nested guards (which inherit these) correctly respect policies.
            object.__setattr__(self, "allowed_inputs", set(final_inputs))
            object.__setattr__(self, "allowed_outputs", set(final_outputs))

            # Create the Rust heart of the guard
            self._inner = _RustContextGuard(
                target=target_obj,
                inputs=final_inputs,
                outputs=final_outputs,
                path_prefix=path_prefix,
                tx=transaction,
                is_admin=False,
                strict_guards=strict_guards,
            )

    def _is_allowed(self, path: str, mode: str = "read") -> bool:
        """[v3.2] Granular check for path access (supports wildcards)."""
        if self._local_is_admin: return True
        # If whitelists are None (e.g. legacy/manual mode), allow all
        # Use getattr to avoid recursion in __getattr__
        inputs = getattr(self, "allowed_inputs", None)
        outputs = getattr(self, "allowed_outputs", None)
        
        # [v3.1.1 Legacy] If no whitelists provided (None), we are in permissive mode.
        # But if they are EMPTY set(), we are in strict mode.
        if inputs is None and mode == "read": return True
        if outputs is None and mode == "write": return True
        
        if mode == "read":
            # [v3.2] READ DISCOVERY: Allow access to parent paths if ANY sub-path is in inputs OR outputs.
            # This is necessary for write-chains like ctx.domain.key = val where ctx.domain must be reachable.
            all_patterns = (inputs or set()) | (outputs or set())
            if "*" in all_patterns: return True
            
            import fnmatch
            norm_path = path.replace("[", ".").replace("]" , "")
            for pattern in all_patterns:
                 norm_pattern = pattern.replace("[", ".").replace("]" , "")
                 if fnmatch.fnmatch(norm_path, norm_pattern): return True
                 if norm_path.startswith(norm_pattern + "."): return True
                 if norm_pattern.startswith(norm_path + "."): return True
            return False
            
        # WRITE MODE: Strict check against outputs only
        targets = outputs
        if targets is None: return True # Permissive if not set
        if "*" in targets: return True
        
        import fnmatch
        norm_path = path.replace("[", ".").replace("]" , "")
        for pattern in targets:
             norm_pattern = pattern.replace("[", ".").replace("]" , "")
             if fnmatch.fnmatch(norm_path, norm_pattern): return True
             if norm_path.startswith(norm_pattern + "."): return True
             # We generally DON'T allow parent-path discovery for WRITE if it's not the exact target
             # because writing to 'domain' would overwrite everything. 
             # But setattr(ctx.domain, "key", val) is a write to "domain.key".
        return False

    @property
    def is_admin(self) -> bool:
        """[RFC-001] Check if this guard is in Admin (Bypass) mode."""
        return self._local_is_admin

    @property
    def is_proxy(self) -> bool:
        return True

    def _elevate(self, enabled: bool):
        """[RFC-001] Explicitly elevate/reset admin status on inner guard."""
        object.__setattr__(self, "_local_is_admin", enabled)
        
        # 1. Elevate the Rust heart (if it's a ContextGuard)
        if isinstance(self._inner, _RustContextGuard):
            if hasattr(self._inner, "_elevate"):
                try: self._inner._elevate(enabled)
                except (AttributeError, PermissionError): pass
            else:
                try: self._inner.is_admin = enabled
                except (AttributeError, PermissionError): pass
        
        # NOTE: We DO NOT aggressively propagate to native proxies here (e.g. setting 'capabilities')
        # because that triggers ContractViolationError if the proxy-path is not in outputs.
        # Instead, we use Parent-Level Overwrite in destructive methods (clear/pop/remove).

    def __getattr__(self, name: str) -> Any:
        # 1. Immediate bypass for whitelisted Python-side attributes
        if name in ("_inner", "_local_is_admin", "log", "_elevate", "is_admin", "is_proxy", "_outbox", "path_prefix", "allowed_inputs", "allowed_outputs", "transaction", "strict_guards"):
            return object.__getattribute__(self, name)

        full_path = name if self.path_prefix == "" else f"{self.path_prefix}.{name}"
        if not self._is_allowed(full_path, "read"):
             # For discovery, we allow 'domain' or 'global' prefixes even if not explicitly in inputs, 
             # provided a sub-path IS allowed. _is_allowed already handles this parent-path check.
             raise PermissionError(f"Illegal Read: Path '{full_path}' is restricted by Process Contract.")

        val = None
        # 2. Rust delegation
        try:
            val = getattr(self._inner, name) if self._inner is not None else None
            if val is None and self._target:
                 # Try target (Hybrid Bridge)
                 val = getattr(self._target, name, None)
        except AttributeError:
             # [RFC-002] Support attribute-style access for DICT proxies or items (e.g. state.domain.balance)
            if hasattr(self._inner, "__getitem__") and not name.startswith("_"):
                 try:
                     return self._inner[name]
                 except (KeyError, TypeError, AttributeError):
                     pass
             
            # [RFC-002] Dynamic Namespace Fallback
            # [RFC-002] Dynamic Namespace Fallback
            from .context import NamespaceRegistry
            if name in NamespaceRegistry()._namespaces:
                try:
                    # Reach into Rust Core: ProcessContext -> State -> Data
                    pc = self._inner._target
                    state_data = pc.state.data
                    val = state_data[name]
                    
                    full_path = name if self.path_prefix == "" else f"{self.path_prefix}.{name}"
                    
                    if isinstance(val, (dict, list)):
                        return ContextGuard(
                            target_obj=None,
                            allowed_inputs=self.allowed_inputs,
                            allowed_outputs=self.allowed_outputs,
                            path_prefix=full_path,
                            transaction=self.transaction,
                            strict_guards=self.strict_guards,
                            process_name=self.log.extra.get("process_name", "Unknown"),
                            _inner=val,
                            parent=self,
                            name=name,
                        )
                    return val
                except Exception:
                    raise
            
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        except PermissionError as e:
            raise e
        
        if self._local_is_admin:
            # 1. Aggressive Propagate Elevation to Rust Proxy
            for attr in ["capabilities", "_capabilities", "caps"]:
                 if hasattr(val, attr):
                      try: setattr(val, attr, 31)
                      except: pass

            # 2. Return elevated wrapper
            if not isinstance(val, ContextGuard) and not isinstance(val, (int, float, str, bool, type(None))):
                 # RECONCILE INNER PROXY (Hybrid Bridge)
                 sub_inner = getattr(val, "_theus_proxy", None)
                 new_guard = ContextGuard(
                    target_obj=val,
                    allowed_inputs=self.allowed_inputs,
                    allowed_outputs=self.allowed_outputs,
                    _inner=sub_inner or val, # Use proxy if available, else native
                    process_name=self.log.extra.get("process_name", "Unknown"),
                    transaction=self.transaction,
                    parent=self,
                    name=name,
                )
                 new_guard._elevate(True)
                 return new_guard
        
        # 4. Nested Guard wrapping (Normal flow)
        if isinstance(val, _RustContextGuard):
            return ContextGuard(
                target_obj=None,
                allowed_inputs=set(),
                allowed_outputs=set(),
                _inner=val,
                process_name=self.log.extra.get("process_name", "Unknown"),
                transaction=self.transaction,
                parent=self,
                name=name,
            )
        return val

    def __getitem__(self, key: Any) -> Any:
        full_path = str(key) if self.path_prefix == "" else f"{self.path_prefix}[{key}]"
        if isinstance(key, str) and not self._is_allowed(full_path, "read"):
             raise PermissionError(f"Illegal Read: Path '{full_path}' is restricted by Process Contract.")

        val = None
        try:
            val = self._inner[key]
        except (PermissionError, AttributeError, KeyError, IndexError, TypeError) as e:
            # [RFC-002] Dynamic Namespace Fallback for Item Access
            if isinstance(key, str):
                from .context import NamespaceRegistry
                if key in NamespaceRegistry()._namespaces:
                    try:
                         # Attempt to reach into Rust Core for Namespace resolution
                         pc = getattr(self._inner, "_target", None)
                         if pc:
                            state_data = pc.state.data
                            val = state_data[key]
                            
                            full_path = key if self.path_prefix == "" else f"{self.path_prefix}.{key}"
                            
                            if isinstance(val, (dict, list)):
                                return ContextGuard(
                                    target_obj=None,
                                    allowed_inputs=self.allowed_inputs,
                                    allowed_outputs=self.allowed_outputs,
                                    path_prefix=full_path,
                                    transaction=self.transaction,
                                    strict_guards=self.strict_guards,
                                    process_name=self.log.extra.get("process_name", "Unknown"),
                                    _inner=val,
                                    parent=self,
                                    name=key,
                                )
                            return val
                    except Exception:
                        pass
            raise e

        if self._local_is_admin:
            if not isinstance(val, ContextGuard) and not isinstance(val, (int, float, str, bool, type(None))):
                 sub_inner = getattr(val, "_theus_proxy", None)
                 new_guard = ContextGuard(
                    target_obj=val,
                    allowed_inputs=self.allowed_inputs,
                    allowed_outputs=self.allowed_outputs,
                    _inner=sub_inner or val,
                    process_name=self.log.extra.get("process_name", "Unknown"),
                    transaction=self.transaction,
                    parent=self,
                    name=key,
                )
                 new_guard._elevate(True)
                 return new_guard

        return val

    # [RFC-001] SHADOW METHODS FOR ADMIN BYPASS
    # We must intercept methods that check capabilities internally in Rust.

    def clear(self):
        if hasattr(self._inner, "clear"):
            try:
                return self._inner.clear()
            except (PermissionError, AttributeError) as e:
                if self._local_is_admin:
                     # FORCE CLEAR via parent-level assignment
                     try:
                         if self.parent:
                             # Overwrite on parent (bypass native child clear)
                             if hasattr(self.parent, "__setitem__"):
                                 self.parent[self.name] = []
                             else:
                                 setattr(self.parent, self.name, [])
                             return None
                     except: pass
                raise e
        return None

    def pop(self, *args, **kwargs):
        if hasattr(self._inner, "pop"):
            try:
                return self._inner.pop(*args, **kwargs)
            except (PermissionError, AttributeError) as e:
                if self._local_is_admin:
                     # Emulate pop via slice deletion
                     try:
                         if len(args) == 0:
                              val = self._inner[-1]
                              del self._inner[-1]
                         else:
                              val = self._inner[args[0]]
                              del self._inner[args[0]]
                         return val
                     except: pass
                raise e
        return None

    def remove(self, *args, **kwargs):
        if hasattr(self._inner, "remove"):
            try:
                return self._inner.remove(*args, **kwargs)
            except (PermissionError, AttributeError) as e:
                if self._local_is_admin:
                     # Emulate remove via index/del
                     try:
                         idx = self._inner.index(args[0])
                         del self._inner[idx]
                         return None
                     except: pass
                raise e
        return None

    def __setattr__(self, name: str, value: Any) -> None:
        if name in ("_inner", "_local_is_admin", "log", "_outbox", "path_prefix", "allowed_inputs", "allowed_outputs", "transaction", "strict_guards", "parent", "name"):
            object.__setattr__(self, name, value)
            return

        full_path = name if self.path_prefix == "" else f"{self.path_prefix}.{name}"
        if not self._is_allowed(full_path, "write"):
             raise PermissionError(f"Illegal Write: Path '{full_path}' is restricted by Process Contract.")

        # Unwrap Python ContextGuard before passing to Rust
        if isinstance(value, ContextGuard):
            value = value._inner
            
        # Support attribute-style access for dict keys
        if isinstance(self._inner, dict):
            self._inner[name] = value
        else:
            setattr(self._inner, name, value)

    def __setitem__(self, key: Any, value: Any) -> None:
        full_path = str(key) if self.path_prefix == "" else f"{self.path_prefix}[{key}]"
        if isinstance(key, str) and not self._is_allowed(full_path, "write"):
             raise PermissionError(f"Illegal Write: Path '{full_path}' is restricted by Process Contract.")

        if isinstance(value, ContextGuard):
            value = value._inner
        
        try:
            self._inner[key] = value
        except (TypeError, AttributeError):
            # Support attribute-style write if not subscriptable
            if isinstance(key, str):
                setattr(self._inner, key, value)
            else:
                raise

    def __iter__(self):
        return iter(self._inner)

    def __contains__(self, item):
        return item in self._inner

    def __len__(self):
        return len(self._inner)

    def __repr__(self):
        return f"<ContextGuard wrapping {repr(self._inner)} admin={self._local_is_admin}>"
