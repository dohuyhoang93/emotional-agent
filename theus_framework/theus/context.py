from dataclasses import dataclass, field
from typing import Optional, Any, List, Dict
from .locks import LockManager
from .zones import ContextZone, resolve_zone

@dataclass
class TransactionError(Exception):
    pass

try:
    import numpy as np
    from multiprocessing import shared_memory

    def rebuild_shm_array(name, shape, dtype):
        """Helper to reconstruct ShmArray from pickle meta-data."""
        try:
            shm = shared_memory.SharedMemory(name=name)
        except FileNotFoundError:
            # If SHM is gone, return None or empty?
            # For now return None to indicate failure
            return None
        
        # Zero-Copy Re-attach
        raw_arr = np.ndarray(shape, dtype=dtype, buffer=shm.buf)
        return ShmArray(raw_arr, shm=shm)

    class ShmArray(np.ndarray):
        """Numpy Array that keeps the backing SharedMemory object alive."""
        def __new__(cls, input_array, shm=None):
            obj = np.asarray(input_array).view(cls)
            obj.shm = shm
            return obj

        def __array_finalize__(self, obj):
            if obj is None: return
            self.shm = getattr(obj, 'shm', None)
            
        def __reduce__(self):
            """Smart Pickling: Send metadata, not data."""
            if self.shm is None:
                # Fallback to standard pickle if no SHM backing
                return super().__reduce__()
            
            # Send (Function, Args) tuple
            return (rebuild_shm_array, (self.shm.name, self.shape, self.dtype))

except ImportError:
    np = None
    ShmArray = None
    rebuild_shm_array = None

class HeavyZoneWrapper:
    """
    Smart Wrapper for ctx.heavy that handles Zero-Copy interactions.
    If it sees a BufferDescriptor, it auto-converts to memoryview/numpy.
    """
    def __init__(self, data_dict):
        self._data = data_dict

    def __getitem__(self, key):
        val = self._data[key]
        # Check if it's a BufferDescriptor (duck typing or strict check)
        if hasattr(val, 'name') and hasattr(val, 'dtype') and hasattr(val, 'shape'):
             # Lazy Import to avoid overhead if not used
             try:
                 import numpy as np
                 from multiprocessing import shared_memory
             except ImportError:
                 return val # Fallback if numpy not present? Or raise?
             
             # Rehydrate View
             try:
                 shm = shared_memory.SharedMemory(name=val.name)
                 # Note: This is read-only view logic for now
                 # We need to ensure we don't leak SHM handles. 
                 # Python's SharedMemory automatic cleanup is tricky. 
                 # Ideally, we should cache this SHM handle handle.
                 raw_arr = np.ndarray(val.shape, dtype=val.dtype, buffer=shm.buf)
                 # Wrap in ShmArray to keep 'shm' alive
                 return ShmArray(raw_arr, shm=shm)
             except FileNotFoundError:
                 # SHM might be gone
                 return None
        return val
    
    def __setitem__(self, key, value):
        # Write-Through to underlying dict (Transaction Logic handles the rest)
        self._data[key] = value

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
            
    def __contains__(self, key):
        return key in self._data

    def items(self):
        for k in self._data:
            yield k, self[k]
            
    def __repr__(self):
        return f"<HeavyZoneWrapper keys={list(self._data.keys())}>"

@dataclass
class LockedContextMixin:
    """
    Mixin that hooks __setattr__ to enforce LockManager policy.
    Now also supports Zone-aware Persistence (to_dict/from_dict).
    """
    _lock_manager: Optional[LockManager] = field(default=None, repr=False, init=False)

    def set_lock_manager(self, manager: LockManager):
        object.__setattr__(self, "_lock_manager", manager)

    def __setattr__(self, name: str, value: Any):
        # 1. Bypass internal fields
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return

        # 2. Check Lock Manager
        # Use object.__getattribute__ to avoid recursion? No, self._lock_manager is safe if set via object.__setattr__
        # But accessing self._lock_manager inside __setattr__ might trigger __getattr__ loop if not careful?
        # Standard access is fine.
        mgr = getattr(self, "_lock_manager", None)
        if mgr:
            mgr.validate_write(name, self)
            
        # 3. Perform Write
        super().__setattr__(name, value)

    def get_zone(self, key: str) -> ContextZone:
        """
        Resolve the semantic zone of a key.
        """
        return resolve_zone(key)

    @property
    def heavy(self):
        # Auto-Dispatch for Zero-Copy
        return HeavyZoneWrapper(self._state.heavy)

    def to_dict(self, exclude_zones: List[ContextZone] = None) -> Dict[str, Any]:
        """
        Export context state to dictionary, filtering out specified zones.
        Default exclusion: SIGNAL, META, HEAVY (if not specified).
        """
        if exclude_zones is None:
            exclude_zones = [ContextZone.SIGNAL, ContextZone.META, ContextZone.HEAVY]
            
        data = {}
        for k, v in self.__dict__.items():
            if k.startswith("_"): continue
            
            zone = self.get_zone(k)
            if zone in exclude_zones:
                continue
                
            if hasattr(v, 'to_dict'):
                data[k] = v.to_dict(exclude_zones)
            else:
                data[k] = v
                
        return data

    def from_dict(self, data: Dict[str, Any]):
        """
        Load state from dictionary.
        """
        for k, v in data.items():
            if k.startswith("_"): continue
            
            if hasattr(self, k):
                current_val = getattr(self, k)
                if hasattr(current_val, 'from_dict') and isinstance(v, dict):
                    current_val.from_dict(v)
                else:
                    setattr(self, k, v)
            else:
                setattr(self, k, v)


@dataclass
class BaseGlobalContext(LockedContextMixin):
    """
    Base Class cho Global Context (Immutable/Locked).
    """
    pass

@dataclass
class BaseDomainContext(LockedContextMixin):
    """
    Base Class cho Domain Context (Mutable/Locked).
    """
    pass

@dataclass
class BaseSystemContext(LockedContextMixin):
    """
    Base Class cho System Context (Wrapper).
    """
    global_ctx: BaseGlobalContext
    domain_ctx: BaseDomainContext

