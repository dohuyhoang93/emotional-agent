"""
FINAL COMPREHENSIVE FIX:
Add 'domain_ctx' and 'global_ctx' to ALL @process decorators where child paths exist
"""
import re
from pathlib import Path

def comprehensive_fix(filepath):
    """Fix a single file by adding parent context paths"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False
    
    original = content
    
    # Find all @process decorators
    def fix_decorator(match):
        full_decorator = match.group(0)
        
        # Extract inputs
        inputs_match = re.search(r"inputs=\[(.*?)\]", full_decorator, re.DOTALL)
        if inputs_match:
            inputs_str = inputs_match.group(1)
            
            # Check if we need domain_ctx
            has_domain_child = bool(re.search(r"['\"]domain_ctx\.", inputs_str))
            has_domain_parent = bool(re.search(r"['\"]domain_ctx['\"]", inputs_str))
            
            if has_domain_child and not has_domain_parent:
                # Add 'domain_ctx' at the beginning
                new_inputs = "'domain_ctx', " + inputs_str
                full_decorator = full_decorator.replace(
                    f"inputs=[{inputs_str}]",
                    f"inputs=[{new_inputs}]"
                )
            
            # Check if we need global_ctx
            inputs_match2 = re.search(r"inputs=\[(.*?)\]", full_decorator, re.DOTALL)
            if inputs_match2:
                inputs_str2 = inputs_match2.group(1)
                has_global_child = bool(re.search(r"['\"]global_ctx\.", inputs_str2))
                has_global_parent = bool(re.search(r"['\"]global_ctx['\"]", inputs_str2))
                
                if has_global_child and not has_global_parent:
                    new_inputs2 = "'global_ctx', " + inputs_str2
                    full_decorator = full_decorator.replace(
                        f"inputs=[{inputs_str2}]",
                        f"inputs=[{new_inputs2}]"
                    )
        
        # Extract outputs
        outputs_match = re.search(r"outputs=\[(.*?)\]", full_decorator, re.DOTALL)
        if outputs_match:
            outputs_str = outputs_match.group(1)
            
            # Check if we need domain_ctx in outputs
            has_domain_child_out = bool(re.search(r"['\"]domain_ctx\.", outputs_str))
            has_domain_parent_out = bool(re.search(r"['\"]domain_ctx['\"]", outputs_str))
            
            if has_domain_child_out and not has_domain_parent_out:
                new_outputs = "'domain_ctx', " + outputs_str
                full_decorator = full_decorator.replace(
                    f"outputs=[{outputs_str}]",
                    f"outputs=[{new_outputs}]"
                )
            
            # Check if we need global_ctx in outputs
            outputs_match2 = re.search(r"outputs=\[(.*?)\]", full_decorator, re.DOTALL)
            if outputs_match2:
                outputs_str2 = outputs_match2.group(1)
                has_global_child_out = bool(re.search(r"['\"]global_ctx\.", outputs_str2))
                has_global_parent_out = bool(re.search(r"['\"]global_ctx['\"]", outputs_str2))
                
                if has_global_child_out and not has_global_parent_out:
                    new_outputs2 = "'global_ctx', " + outputs_str2
                    full_decorator = full_decorator.replace(
                        f"outputs=[{outputs_str2}]",
                        f"outputs=[{new_outputs2}]"
                    )
        
        return full_decorator
    
    # Pattern to match @process(...) including multi-line
    pattern = r'@process\([^)]*\)'
    content = re.sub(pattern, fix_decorator, content, flags=re.DOTALL)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Find ALL Python files in src directory
base = Path(r"C:\Users\dohuy\Downloads\emotional-agent\src")
all_py_files = list(base.rglob("*.py"))

fixed_count = 0
for filepath in all_py_files:
    if comprehensive_fix(filepath):
        print(f"Fixed: {filepath.relative_to(base)}")
        fixed_count += 1

print(f"\n✅ Total fixed: {fixed_count} files")
