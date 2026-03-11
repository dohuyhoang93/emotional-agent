
path = r'c:\Users\dohoang\projects\EmotionAgent\theus_framework\theus\guards.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

target = 'if isinstance(val, _RustContextGuard) or (hasattr(val, "is_proxy") and getattr(val, "is_proxy")()):'
replacement = 'if (isinstance(val, _RustContextGuard) or (hasattr(val, "is_proxy") and getattr(val, "is_proxy")())) and not isinstance(val, (np.ndarray, torch.Tensor)):'

new_text = text.replace(target, replacement)
count = text.count(target)

with open(path, 'w', encoding='utf-8') as f:
    f.write(new_text)

print(f"Updated {count} instances.")
