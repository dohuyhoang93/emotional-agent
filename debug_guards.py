
path = r'c:\Users\dohoang\projects\EmotionAgent\theus_framework\theus\guards.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'return val' in line and ('__getitem__' in ''.join(lines[max(0, lines.index(line)-20):lines.index(line)])):
         # Find the line before return val in __getitem__
         new_lines.append('        # print(f"DEBUG: __getitem__ returning {type(val)} for key {key} (ContextGuard={isinstance(val, ContextGuard)})")\n')
         new_lines.append(line)
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
