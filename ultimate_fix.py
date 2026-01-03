"""
ULTIMATE FIX: Scan ALL Python files and add parent contexts
This version is more aggressive and handles ALL edge cases
"""
import re
from pathlib import Path

def ultimate_fix(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False
    
    original = content
    
    # Find @process decorators - handle multi-line with better regex
    decorators = list(re.finditer(r'@process\s*\([^@]*?\n\)', content, re.DOTALL))
    
    for match in reversed(decorators):  # Reverse to maintain positions
        decorator = match.group(0)
        new_decorator = decorator
        
        # Extract inputs
        inputs_match = re.search(r'inputs\s*=\s*\[(.*?)\]', decorator, re.DOTALL)
        if inputs_match:
            inputs_str = inputs_match.group(1)
            
            # Add domain_ctx if has domain_ctx.xxx
            if "'domain_ctx." in inputs_str or '"domain_ctx.' in inputs_str:
                if not ("'domain_ctx'" in inputs_str or '"domain_ctx"' in inputs_str):
                    # Add at beginning
                    new_inputs = "'domain_ctx', " + inputs_str
                    new_decorator = new_decorator.replace(
                        f'inputs=[{inputs_str}]',
                        f'inputs=[{new_inputs}]'
                    )
            
            # Re-extract for global_ctx check
            inputs_match2 = re.search(r'inputs\s*=\s*\[(.*?)\]', new_decorator, re.DOTALL)
            if inputs_match2:
                inputs_str2 = inputs_match2.group(1)
                if "'global_ctx." in inputs_str2 or '"global_ctx.' in inputs_str2:
                    if not ("'global_ctx'" in inputs_str2 or '"global_ctx"' in inputs_str2):
                        new_inputs2 = "'global_ctx', " + inputs_str2
                        new_decorator = new_decorator.replace(
                            f'inputs=[{inputs_str2}]',
                            f'inputs=[{new_inputs2}]'
                        )
        
        # Extract outputs
        outputs_match = re.search(r'outputs\s*=\s*\[(.*?)\]', new_decorator, re.DOTALL)
        if outputs_match:
            outputs_str = outputs_match.group(1)
            
            # Add domain_ctx if has domain_ctx.xxx or domain.xxx
            if ("'domain_ctx." in outputs_str or '"domain_ctx.' in outputs_str or 
                "'domain." in outputs_str or '"domain.' in outputs_str):
                if not ("'domain_ctx'" in outputs_str or '"domain_ctx"' in outputs_str):
                    new_outputs = "'domain_ctx', " + outputs_str
                    new_decorator = new_decorator.replace(
                        f'outputs=[{outputs_str}]',
                        f'outputs=[{new_outputs}]'
                    )
            
            # Re-extract for global_ctx
            outputs_match2 = re.search(r'outputs\s*=\s*\[(.*?)\]', new_decorator, re.DOTALL)
            if outputs_match2:
                outputs_str2 = outputs_match2.group(1)
                if ("'global_ctx." in outputs_str2 or '"global_ctx.' in outputs_str2 or
                    "'global." in outputs_str2 or '"global.' in outputs_str2):
                    if not ("'global_ctx'" in outputs_str2 or '"global_ctx"' in outputs_str2):
                        new_outputs2 = "'global_ctx', " + outputs_str2
                        new_decorator = new_decorator.replace(
                            f'outputs=[{outputs_str2}]',
                            f'outputs=[{new_outputs2}]'
                        )
        
        if new_decorator != decorator:
            content = content[:match.start()] + new_decorator + content[match.end():]
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Process ALL
base = Path(r"C:\Users\dohuy\Downloads\emotional-agent\src")
files = list(base.rglob("*.py"))

fixed = 0
for f in files:
    if ultimate_fix(f):
        print(f"Fixed: {f.relative_to(base)}")
        fixed += 1

print(f"\n✅ Total: {fixed} files")
