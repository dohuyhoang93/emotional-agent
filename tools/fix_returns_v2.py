import json
import os

with open('linter_report.json', 'r', encoding='utf-8') as f:
    data = f.read()

reports = []
for line in data.split('\n'):
    if line.startswith('['):
        try:
            reports.extend(json.loads(line))
        except: pass

counts = 0
for r in reports:
    if r.get('check_id') == 'POP-E06' and (r['file'].startswith('src') or r['file'].startswith('demo_client')):
        file_path = r['file']
        line_idx = r['line'] - 1 # 0-indexed
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        original_line = lines[line_idx]
        if 'return' in original_line and 'return {}' not in original_line and 'return ' not in original_line:
            # It's an empty return. e.g. "        return\n"
            lines[line_idx] = original_line.replace('return', 'return {}')
            counts += 1
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        elif 'return' not in original_line:
            # Usually happens if the AST points to function def/end but there's no return at all.
            # Wait, the error is 'Found empty return.' or 'must have an explicit return statement (Delta)'
            if 'Found empty return' in r.get('message', ''):
                pass # Already handled or format mismatch
            elif 'must have an explicit return statement' in r.get('message', ''):
                # We need to append `return {}` at the end of the function.
                # We can't do it blindly by AST in this script easily without 'ast' module, but we already have our fix_returns.py which we can run again? No, fix_returns.py missed them. Let's let fix_returns.py handle or we just do it manually.
                pass

print(f"Fixed {counts} empty returns based on JSON line numbers.")
