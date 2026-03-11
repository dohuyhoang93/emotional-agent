
import re

path = r'c:\Users\dohoang\projects\EmotionAgent\theus_framework\theus\guards.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix __getattr__
getattr_target = re.escape('raise PermissionError(f"Illegal Read: Path \'{full_path}\' is restricted by Process Contract.")') + r'\s+' + re.escape('val = None')
getattr_replacement = 'raise PermissionError(f"Illegal Read: Path \'{full_path}\' is restricted by Process Contract.")\n\n        # 0. Heavy Zone Bypassing (Zero-Copy)\n        if name.startswith("heavy_"):\n            val = getattr(self._inner, name, None) if self._inner is not None else None\n            if val is None and self._target:\n                 val = getattr(self._target, name, None)\n            if val is not None:\n                return val\n\n        val = None'

# Fix __getitem__
getitem_target = re.escape('raise PermissionError(f"Illegal Read: Path \'{full_path}\' is restricted by Process Contract.")') + r'\s+' + re.escape('val = None')
# Wait, __getitem__ has the same pattern. re.sub with count=1 might be safer if I do it twice or use specific markers.

# Let's use a more robust way: find the start of the methods.
# For __getattr__
content = re.sub(
    r'(def __getattr__\(self, name: str\) -> Any:.*?val = None)',
    r'\1\n        # 0. Heavy Zone Bypassing (Zero-Copy)\n        if name.startswith("heavy_"):\n            val = getattr(self._inner, name, None) if self._inner is not None else None\n            if val is None and self._target:\n                 val = getattr(self._target, name, None)\n            if val is not None:\n                return val',
    content,
    flags=re.DOTALL,
    count=1
)

# For __getitem__
content = re.sub(
    r'(def __getitem__\(self, key: Any\) -> Any:.*?val = None)',
    r'\1\n        # 0. Heavy Zone Bypassing (Zero-Copy)\n        if isinstance(key, str) and key.startswith("heavy_"):\n            try:\n                val = self._inner[key]\n                return val\n            except: pass',
    content,
    flags=re.DOTALL,
    count=1
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Successfully updated guards.py with heavy_ bypassing.")
