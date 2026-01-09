"""
Systematic fix for all process files:
Add 'domain_ctx' and 'global_ctx' to inputs/outputs where child paths are used
"""
import re
from pathlib import Path

def fix_process_contracts(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    
    # Pattern to find @process decorators
    pattern = r'@process\((.*?)\n\)'
    
    def fix_decorator(match):
        full_match = match.group(0)
        decorator_args = match.group(1)
        
        # Extract inputs and outputs
        inputs_match = re.search(r"inputs=\[(.*?)\]", decorator_args, re.DOTALL)
        outputs_match = re.search(r"outputs=\[(.*?)\]", decorator_args, re.DOTALL)
        
        if not inputs_match:
            return full_match
        
        inputs_str = inputs_match.group(1)
        
        # Check if we need to add domain_ctx/global_ctx
        needs_domain = bool(re.search(r"['\"]domain_ctx\.", inputs_str))
        needs_global = bool(re.search(r"['\"]global_ctx\.", inputs_str))
        
        has_domain = "'domain_ctx'" in inputs_str or '"domain_ctx"' in inputs_str
        has_global = "'global_ctx'" in inputs_str or '"global_ctx"' in inputs_str
        
        # Add to inputs if needed
        if needs_domain and not has_domain:
            inputs_str = "'domain_ctx', " + inputs_str
        if needs_global and not has_global:
            inputs_str = "'global_ctx', " + inputs_str
        
        new_decorator = decorator_args.replace(inputs_match.group(0), f"inputs=[{inputs_str}]")
        
        # Same for outputs
        if outputs_match:
            outputs_str = outputs_match.group(1)
            needs_domain_out = bool(re.search(r"['\"]domain_ctx\.", outputs_str)) or bool(re.search(r"['\"]domain\.", outputs_str))
            needs_global_out = bool(re.search(r"['\"]global_ctx\.", outputs_str)) or bool(re.search(r"['\"]global\.", outputs_str))
            
            has_domain_out = "'domain_ctx'" in outputs_str or '"domain_ctx"' in outputs_str or "'domain'" in outputs_str
            has_global_out = "'global_ctx'" in outputs_str or '"global_ctx"' in outputs_str or "'global'" in outputs_str
            
            if needs_domain_out and not has_domain_out:
                outputs_str = "'domain_ctx', " + outputs_str
            if needs_global_out and not has_global_out:
                outputs_str = "'global_ctx', " + outputs_str
            
            new_decorator = new_decorator.replace(outputs_match.group(0), f"outputs=[{outputs_str}]")
        
        return f"@process({new_decorator}\n)"
    
    content = re.sub(pattern, fix_decorator, content, flags=re.DOTALL)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Process all files
base = Path(r"C:\Users\dohuy\Downloads\emotional-agent\src")
files = list(base.rglob("p*.py")) + list(base.rglob("*processes*.py"))

fixed = 0
for f in files:
    if fix_process_contracts(f):
        print(f"Fixed: {f.name}")
        fixed += 1

print(f"\nTotal: {fixed} files")
