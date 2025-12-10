from typing import Any, Set
from .contracts import ContractViolationError

class ContextGuard:
    """
    Proxy bảo vệ Context tại Runtime.
    1. Chặn Ghi (setattr) vào biến không có trong outputs.
    2. Chặn Đọc (getattr) biến không có trong inputs.
    """
    def __init__(self, target_obj: Any, allowed_inputs: Set[str], allowed_outputs: Set[str], path_prefix: str = ""):
        # Use object.__setattr__ to avoid recursion during init
        object.__setattr__(self, "_target_obj", target_obj)
        object.__setattr__(self, "_allowed_inputs", allowed_inputs)
        object.__setattr__(self, "_allowed_outputs", allowed_outputs)
        object.__setattr__(self, "_path_prefix", path_prefix)

    def __getattr__(self, name: str):
        # 1. System/Magic Attribute Bypass
        # Allow Python internal attributes (e.g. __class__, _pytest_fixture)
        if name.startswith("_"):
             return getattr(self._target_obj, name)

        # 2. Navigation Logic (Layer Containers)
        # We assume accessing a Layer Container (e.g. domain_ctx) is always allowed/safe
        # so we can traverse deeper to check the actual leaf variable.
        if name.endswith("_ctx"):
             val = getattr(self._target_obj, name)
             # Logic: layer name inference. 
             # domain_ctx -> "domain"
             next_prefix = name.replace("_ctx", "")
             return ContextGuard(val, self._allowed_inputs, self._allowed_outputs, next_prefix)

        # 3. Leaf / Primitive Attribute Logic
        full_path = f"{self._path_prefix}.{name}" if self._path_prefix else name
            
        # READ GUARD
        # Rule: Full path must be in inputs OR a parent path is in inputs
        parts = full_path.split('.')
        parent_paths = ['.'.join(parts[:i]) for i in range(1, len(parts))]
        
        is_allowed = (
            full_path in self._allowed_inputs or 
            any(p in self._allowed_inputs for p in parent_paths)
        )
        
        if not is_allowed:
             raise ContractViolationError(
                f"Illegal Read Violation: Process attempted to read '{full_path}' "
                f"but it was not declared in inputs=[...]."
            )
        
        # Safe to read now
        return getattr(self._target_obj, name)

    def __setattr__(self, name: str, value: Any):
        full_path = f"{self._path_prefix}.{name}" if self._path_prefix else name
            
        # WRITE GUARD
        if full_path not in self._allowed_outputs:
            raise ContractViolationError(
                f"Illegal Write Violation: Process attempted to modify '{full_path}' "
                f"but it was not declared in outputs=[...]."
            )
            
        setattr(self._target_obj, name, value)
