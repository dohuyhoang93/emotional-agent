from typing import Any
# Re-export from Rust Core
try:
    from theus_core import ConfigLoader, SchemaViolationError, AuditRecipe
except ImportError:
    class SchemaViolationError(Exception): pass
    class AuditRecipe:
        def __init__(self, threshold_max=3, reset_on_success=True): pass
    class ConfigLoader:
        @staticmethod
        def load_from_string(content: str): pass

class ConfigFactory:
    @staticmethod
    def load_recipe(path: str):
        import yaml
        import os
        if not os.path.exists(path):
            raise FileNotFoundError(f"Recipe not found: {path}")
            
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
            
        # Map fields to AuditRecipe
        # V2 YAML might have different structure.
        # We look for keys matching AuditRecipe fields.
        # Defaults: threshold_max=3, reset_on_success=True
        
        # If 'audit' key exists, use it?
        target = data
        if 'audit' in data:
            target = data['audit']
            
        t_max = target.get('threshold_max', target.get('max_retries', 3))
        reset = target.get('reset_on_success', True)
        
        return AuditRecipe(threshold_max=int(t_max), reset_on_success=bool(reset))

__all__ = ["ConfigLoader", "SchemaViolationError", "ConfigFactory", "AuditRecipe"]
