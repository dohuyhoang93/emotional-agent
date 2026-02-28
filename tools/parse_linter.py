import sys

try:
    with open('linter_report_v2.txt', 'r', encoding='utf-16') as f: lines = f.readlines()
except:
    with open('linter_report_v2.txt', 'r', encoding='utf-8') as f: lines = f.readlines()

output = []
for line in lines:
    if '│' in line:
        parts = [p.strip() for p in line.split('│')]
        if len(parts) >= 4:
            loc = parts[1]
            if loc.startswith('src') or loc.startswith('demo_client'):
                output.append(f'{loc} | {parts[2]} | {parts[3]}')

with open('filtered_linter.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('Filtered linter written successfully.')
