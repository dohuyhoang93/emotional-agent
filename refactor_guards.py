import os
import re

file_path = os.path.join("theus_framework", "theus", "guards.py")
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace assignments in __init__
content = content.replace('self.log =', 'object.__setattr__(self, "_log",')
content = content.replace('self.log.extra =', 'self._log.extra =')
content = content.replace('self.log.warning', 'self._log.warning')

# Replace object.__setattr__ logic
content = content.replace('object.__setattr__(self, "path_prefix"', 'object.__setattr__(self, "_path_prefix"')
content = content.replace('object.__setattr__(self, "allowed_inputs"', 'object.__setattr__(self, "_allowed_inputs"')
content = content.replace('object.__setattr__(self, "allowed_outputs"', 'object.__setattr__(self, "_allowed_outputs"')
content = content.replace('object.__setattr__(self, "transaction"', 'object.__setattr__(self, "_transaction"')
content = content.replace('object.__setattr__(self, "strict_guards"', 'object.__setattr__(self, "_strict_guards"')
content = content.replace('object.__setattr__(self, "parent"', 'object.__setattr__(self, "_parent"')
content = content.replace('object.__setattr__(self, "name"', 'object.__setattr__(self, "_name"')

# Replace getattr and self. access
content = content.replace('getattr(self, "allowed_inputs"', 'getattr(self, "_allowed_inputs"')
content = content.replace('getattr(self, "allowed_outputs"', 'getattr(self, "_allowed_outputs"')

# Replace direct references
content = re.sub(r'\bself\.path_prefix\b', 'self._path_prefix', content)
content = re.sub(r'\bself\.allowed_inputs\b', 'self._allowed_inputs', content)
content = re.sub(r'\bself\.allowed_outputs\b', 'self._allowed_outputs', content)
content = re.sub(r'\bself\.transaction\b', 'self._transaction', content)
content = re.sub(r'\bself\.strict_guards\b', 'self._strict_guards', content)
content = re.sub(r'\bself\.parent\b', 'self._parent', content)
content = re.sub(r'\bself\.name\b', 'self._name', content)
content = re.sub(r'\bself\.log\b', 'self._log', content)

# Fix __init__ kwargs propagation
content = re.sub(r'process_name=self\._log\.extra\.get\("process_name"', 'process_name=self._log.extra.get("process_name"', content)

# Fix __getattr__ whitelist
old_whitelist = '("_inner", "_local_is_admin", "log", "_elevate", "is_admin", "is_proxy", "_outbox", "path_prefix", "allowed_inputs", "allowed_outputs", "transaction", "strict_guards", "_target")'
new_whitelist = '("_inner", "_local_is_admin", "_log", "_elevate", "is_admin", "is_proxy", "_outbox", "_path_prefix", "_allowed_inputs", "_allowed_outputs", "_transaction", "_strict_guards", "_parent", "_name", "_target")'
content = content.replace(old_whitelist, new_whitelist)

# Fix __setattr__ whitelist
old_setattr_wl = '("_inner", "_local_is_admin", "log", "_outbox", "path_prefix", "allowed_inputs", "allowed_outputs", "transaction", "strict_guards", "parent", "name")'
new_setattr_wl = '("_inner", "_local_is_admin", "_log", "_outbox", "_path_prefix", "_allowed_inputs", "_allowed_outputs", "_transaction", "_strict_guards", "_parent", "_name", "_target")'
content = content.replace(old_setattr_wl, new_setattr_wl)

# One extra manual fix for the object.__setattr__(self, "_log", logging...) missing parenthesis
content = content.replace('object.__setattr__(self, "_log", logging.getLogger("theus.guards")', 'object.__setattr__(self, "_log", logging.getLogger("theus.guards"))')

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Guards refactored successfully.")
