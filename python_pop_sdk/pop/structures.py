from typing import Any, List, Dict, Union, MutableSequence, MutableMapping
from .delta import Transaction, DeltaEntry

class TrackedList(MutableSequence):
    """
    A smart wrapper around a list that logs all mutations to a Transaction.
    It operates on a 'Shadow List', ensuring isolation.
    """
    def __init__(self, shadow_list: List, transaction: Transaction, path: str):
        self._data = shadow_list
        self._tx = transaction
        self._path = path

    # --- MutableSequence Abstract Methods ---
    # --- MutableSequence Abstract Methods ---
    def __getitem__(self, index):
        val = self._data[index]
        # Recursively wrap List/Dict
        if isinstance(val, (list, dict)):
            # 1. Get/Create Shadow for the child
            shadow_child = self._tx.get_shadow(val)
            
            # 2. Update Link (Lazy Deepening)
            if shadow_child is not val:
                 self._data[index] = shadow_child
                 
            # 3. Return Wrapped
            child_path = f"{self._path}[{index}]"
            if isinstance(shadow_child, list):
                return TrackedList(shadow_child, self._tx, child_path)
            elif isinstance(shadow_child, dict):
                return TrackedDict(shadow_child, self._tx, child_path)
                
        return val

    def __setitem__(self, index, value):
        old_val = self._data[index]
        self._data[index] = value
        
        # Log Logic: path[index]
        entry_path = f"{self._path}[{index}]"
        self._tx.log(DeltaEntry(entry_path, "SET", value, old_val))

    def __delitem__(self, index):
        old_val = self._data[index]
        del self._data[index]
        
        entry_path = f"{self._path}[{index}]"
        self._tx.log(DeltaEntry(entry_path, "REMOVE", None, old_val))

    def __len__(self):
        return len(self._data)

    def insert(self, index, value):
        self._data.insert(index, value)
        # Log INSERT is complex for paths, but we simplify to "INSERT" op
        self._tx.log(DeltaEntry(f"{self._path}", "INSERT", (index, value)))

    # --- Optimizations / Overrides ---
    def append(self, value):
        self._data.append(value)
        self._tx.log(DeltaEntry(self._path, "APPEND", value))
        
    def extend(self, values):
        self._data.extend(values)
        self._tx.log(DeltaEntry(self._path, "EXTEND", values))
        
    def pop(self, index=-1):
        val = self._data.pop(index)
        self._tx.log(DeltaEntry(self._path, "POP", index, val))
        return val
        
    def __repr__(self):
        return repr(self._data)
        
    def __str__(self):
        return str(self._data)


class TrackedDict(MutableMapping):
    """
    A smart wrapper around a dict that logs all mutations.
    """
    def __init__(self, shadow_dict: Dict, transaction: Transaction, path: str):
        self._data = shadow_dict
        self._tx = transaction
        self._path = path

    def __getitem__(self, key):
        val = self._data[key]
        if isinstance(val, (list, dict)):
            shadow_child = self._tx.get_shadow(val)
            
            if shadow_child is not val:
                 self._data[key] = shadow_child
            
            entry_path = f"{self._path}.{key}" if isinstance(key, str) else f"{self._path}[{key}]"
            
            if isinstance(shadow_child, list):
                return TrackedList(shadow_child, self._tx, entry_path)
            elif isinstance(shadow_child, dict):
                return TrackedDict(shadow_child, self._tx, entry_path)
                
        return val

    def __setitem__(self, key, value):
        old_val = self._data.get(key)
        self._data[key] = value
        
        entry_path = f"{self._path}.{key}" # Dot notation for dict keys? Or ['key']?
        # Let's use dot for string keys, bracket for others? 
        # For simplicity in POP (which implies JSON-like context), keys are usually strings.
        entry_path = f"{self._path}.{key}" if isinstance(key, str) else f"{self._path}[{key}]"
        
        op = "UPDATE" if old_val is not None else "ADD"
        self._tx.log(DeltaEntry(entry_path, "SET", value, old_val))

    def __delitem__(self, key):
        old_val = self._data[key]
        del self._data[key]
        
        entry_path = f"{self._path}.{key}" if isinstance(key, str) else f"{self._path}[{key}]"
        self._tx.log(DeltaEntry(entry_path, "REMOVE", None, old_val))

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)
        
    def __repr__(self):
        return repr(self._data)
