"""
FINAL COMPREHENSIVE FIX - Add ALL missing aliases
This will add BOTH domain_ctx AND domain aliases to all contracts
"""
import re
from pathlib import Path

def add_all_aliases(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False
    
    original = content
    
    # Find all @process decorators
    decorators = list(re.finditer(r'@process\s*\([^@]*?\n\)', content, re.DOTALL))
    
    for match in reversed(decorators):
        decorator = match.group(0)
        new_decorator = decorator
        
        # Fix inputs - add BOTH domain_ctx and domain
        inputs_match = re.search(r'inputs\s*=\s*\[(.*?)\]', decorator, re.DOTALL)
        if inputs_match:
            inputs_str = inputs_match.group(1)
            
            # Check for domain_ctx children
            has_domain_ctx_child = "'domain_ctx." in inputs_str or '"domain_ctx.' in inputs_str
            has_domain_child = "'domain." in inputs_str or '"domain.' in inputs_str
            has_domain_ctx_parent = "'domain_ctx'" in inputs_str or '"domain_ctx"' in inputs_str
            has_domain_parent = "'domain'" in inputs_str or '"domain"' in inputs_str
            
            additions = []
            if (has_domain_ctx_child or has_domain_child) and not has_domain_ctx_parent:
                additions.append("'domain_ctx'")
            if has_domain_child and not has_domain_parent:
                additions.append("'domain'")
            
            if additions:
                new_inputs = ", ".join(additions) + ", " + inputs_str
                new_decorator = new_decorator.replace(
                    f'inputs=[{inputs_str}]',
                    f'inputs=[{new_inputs}]'
                )
            
            # Same for global_ctx
            inputs_match2 = re.search(r'inputs\s*=\s*\[(.*?)\]', new_decorator, re.DOTALL)
            if inputs_match2:
                inputs_str2 = inputs_match2.group(1)
                has_global_ctx_child = "'global_ctx." in inputs_str2 or '"global_ctx.' in inputs_str2
                has_global_child = "'global." in inputs_str2 or '"global.' in inputs_str2
                has_global_ctx_parent = "'global_ctx'" in inputs_str2 or '"global_ctx"' in inputs_str2
                has_global_parent = "'global'" in inputs_str2 or '"global"' in inputs_str2
                
                additions2 = []
                if (has_global_ctx_child or has_global_child) and not has_global_ctx_parent:
                    additions2.append("'global_ctx'")
                if has_global_child and not has_global_parent:
                    additions2.append("'global'")
                
                if additions2:
                    new_inputs2 = ", ".join(additions2) + ", " + inputs_str2
                    new_decorator = new_decorator.replace(
                        f'inputs=[{inputs_str2}]',
                        f'inputs=[{new_inputs2}]'
                    )
        
        # Fix outputs - same logic
        outputs_match = re.search(r'outputs\s*=\s*\[(.*?)\]', new_decorator, re.DOTALL)
        if outputs_match:
            outputs_str = outputs_match.group(1)
            
            has_domain_ctx_child = "'domain_ctx." in outputs_str or '"domain_ctx.' in outputs_str
            has_domain_child = "'domain." in outputs_str or '"domain.' in outputs_str
            has_domain_ctx_parent = "'domain_ctx'" in outputs_str or '"domain_ctx"' in outputs_str
            has_domain_parent = "'domain'" in outputs_str or '"domain"' in outputs_str
            
            additions = []
            if (has_domain_ctx_child or has_domain_child) and not has_domain_ctx_parent:
                additions.append("'domain_ctx'")
            if has_domain_child and not has_domain_parent:
                additions.append("'domain'")
            
            if additions:
                new_outputs = ", ".join(additions) + ", " + outputs_str
                new_decorator = new_decorator.replace(
                    f'outputs=[{outputs_str}]',
                    f'outputs=[{new_outputs}]'
                )
            
            # Same for global
            outputs_match2 = re.search(r'outputs\s*=\s*\[(.*?)\]', new_decorator, re.DOTALL)
            if outputs_match2:
                outputs_str2 = outputs_match2.group(1)
                has_global_ctx_child = "'global_ctx." in outputs_str2 or '"global_ctx.' in outputs_str2
                has_global_child = "'global." in outputs_str2 or '"global.' in outputs_str2
                has_global_ctx_parent = "'global_ctx'" in outputs_str2 or '"global_ctx"' in outputs_str2
                has_global_parent = "'global'" in outputs_str2 or '"global"' in outputs_str2
                
                additions2 = []
                if (has_global_ctx_child or has_global_child) and not has_global_ctx_parent:
                    additions2.append("'global_ctx'")
                if has_global_child and not has_global_parent:
                    additions2.append("'global'")
                
                if additions2:
                    new_outputs2 = ", ".join(additions2) + ", " + outputs_str2
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

# Process ALL files
base = Path(r"C:\Users\dohuy\Downloads\emotional-agent\src")
files = list(base.rglob("*.py"))

fixed = 0
for f in files:
    if add_all_aliases(f):
        print(f"Fixed: {f.relative_to(base)}")
        fixed += 1

print(f"\n✅ Total: {fixed} files")
