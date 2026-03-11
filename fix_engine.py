
path = r'c:\Users\dohoang\projects\EmotionAgent\theus_framework\theus\engine.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
count = 0
for line in lines:
    if 'target_obj=ctx,' in line:
        new_lines.append(line.replace('target_obj=ctx,', 'target_obj=self._context,'))
        count += 1
    else:
        new_lines.append(line)

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"Updated {count} instances.")
