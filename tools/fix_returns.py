import os
import ast

def fix_missing_returns(directory):
    count = 0
    for root, _, fs in os.walk(directory):
        for f in fs:
            if not f.endswith('.py'): continue
            filepath = os.path.join(root, f)
            with open(filepath, 'r', encoding='utf-8') as file:
                source = file.read()
            try:
                tree = ast.parse(source)
            except Exception:
                continue
            
            with open(filepath, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                
            modifications = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    has_process = False
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call) and getattr(dec.func, 'id', '') == 'process': has_process = True
                        elif isinstance(dec, ast.Name) and dec.id == 'process': has_process = True
                    
                    if has_process and node.body:
                        last_stmt = node.body[-1]
                        if not isinstance(last_stmt, ast.Return):
                            end_line = getattr(last_stmt, 'end_lineno', last_stmt.lineno)
                            indent = ' ' * last_stmt.col_offset
                            modifications.append((end_line, f'{indent}return {{}}\n'))
                        elif last_stmt.value is None:
                            lineno = last_stmt.lineno - 1
                            lines[lineno] = lines[lineno].rstrip() + ' {}\n'
                            count += 1
            
            if modifications:
                modifications.sort(key=lambda x: x[0], reverse=True)
                for line_no, text in modifications:
                    lines.insert(line_no, text)
                    count += 1
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                print(f'Fixed missing returns in {filepath}')
            elif count > 0:
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.writelines(lines)
                print(f'Updated empty returns in {filepath}')
    return count

print("Fixed orchestrator processes returns:", fix_missing_returns("src/orchestrator/processes"))
print("Fixed source processes returns:", fix_missing_returns("src/processes"))
print("Fixed legacy processes returns:", fix_missing_returns("src/legacy_archive/processes"))
print("Fixed demo client processes returns:", fix_missing_returns("demo_client/src/processes"))
