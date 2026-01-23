"""
THEUS SUPERVISOR PROTOTYPE (Mock)
=================================
This module simulates the proposed "Supervisor Architecture" where:
1. Data resides in Python Heap (Mocked as a dict of references).
2. "Rust Core" (Mocked here) manages Metadata (Lock, Version) only.

Target: Verify if "GIL Contention" (Lock) is faster than "Serialization" (Deep Copy).
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from contextlib import contextmanager

@dataclass
class SupervisorEntry:
    """
    Represents what the Rust Core would hold:
    - A pointer to the Python Object (self.ref)
    - Metadata (version, lock)
    """
    ref: Any  # In Rust this would be Py<PyAny>
    version: int = 0
    lock: threading.Lock = field(default_factory=threading.Lock)

class SupervisorProxy:
    """
    The Gatekeeper.
    User code only ever sees this Proxy, never the raw SupervisorEntry.
    """
    def __init__(self, engine: 'SupervisorEngine', key: str, ref: Any):
        # Hidden attributes (use name mangling or special prefix to hide)
        object.__setattr__(self, '_engine', engine)
        object.__setattr__(self, '_key', key)
        object.__setattr__(self, '_ref', ref)
    
    def __getattr__(self, name):
        # 1. READ: Delegate to internal ref (Fast-ish)
        return getattr(self._ref, name)
    
    def __setattr__(self, name, value):
        # 2. WRITE INTERCEPTION
        # We assume ANY attribute set on the proxy is an intent to mutate state
        key = self._key
        
        # Security Check (Mock: Only allow if key starts with 'safe_')
        # In reality this would check Current Process Token vs Schema
        if not self._engine.is_authorized(key, "write"):
            raise PermissionError(f"Security Violation: Modify '{key}' is forbidden.")
            
        # Supervisor Logic: We must update the whole object or just this field?
        # For this prototype: We do a simplified Field Update via Engine
        # In full version: Engine.compare_and_swap_field(key, field, val)
        print(f"[Supervisor] Intercepted write to {key}.{name} = {value}")
        
        # Forward modification to Engine (which holds the Lock)
        # Here we just mutate directly under lock for simplicity of prototype
        entry = self._engine._get_entry(key)
        with entry.lock:
             setattr(self._ref, name, value)
             entry.version += 1

class SupervisorEngine:
    """
    Simulates the Rust Core acting as a Supervisor.
    """
    def __init__(self, init_data: Dict[str, Any] = None):
        self._heap: Dict[str, SupervisorEntry] = {}
        if init_data:
            for k, v in init_data.items():
                self._heap[k] = SupervisorEntry(ref=v, version=0)

    def _get_entry(self, key):
        return self._heap[key]

    def is_authorized(self, key: str, action: str) -> bool:
        """Mock Security Policy"""
        # Example: Prevent modifying 'system' keys
        if key.startswith("system"):
            return False
        return True

    def read(self, key: str) -> Any:
        """
        Returns a PROXY, not the raw reference.
        """
        if key not in self._heap:
            return None
        
        entry = self._heap[key]
        # Wrap in Proxy
        return SupervisorProxy(self, key, entry.ref)

    def get_version(self, key: str) -> int:
        if key not in self._heap:
            return -1
        return self._heap[key].version
    
    # ... (compare_and_swap kept for full object replacement) ...
    def compare_and_swap(self, key: str, expected_ver: int, new_val: Any) -> bool:
        if key not in self._heap:
            with threading.Lock():
                 self._heap[key] = SupervisorEntry(ref=new_val, version=0)
            return True

        entry = self._heap[key]
        with entry.lock:
            if entry.version != expected_ver:
                return False
            entry.ref = new_val
            entry.version += 1
            return True

    @contextmanager
    def edit(self, key: str):
        # Deprecated in Supervisor Model? Or returns Proxy?
        # Let's say it returns the Raw Ref for Admin use only
        if key not in self._heap:
            raise KeyError(key)
        entry = self._heap[key]
        with entry.lock:
            yield entry.ref
            entry.version += 1
