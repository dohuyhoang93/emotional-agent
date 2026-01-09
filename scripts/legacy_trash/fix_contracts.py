import re
import sys
from pathlib import Path

def fix_process_file(filepath):
    """Add domain_ctx and global_ctx to inputs if not present"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find @process decorators
    pattern = r"@process\((.*?)\)"
    
    def fix_decorator(match):
        decorator_content = match.group(1)
        
        # Extract inputs list
        inputs_match = re.search(r"inputs=\[(.*?)\]", decorator_content, re.DOTALL)
        if not inputs_match:
            return match.group(0)
        
        inputs_str = inputs_match.group(1)
        
        # Check if domain_ctx or global_ctx already present
        has_domain_ctx = "'domain_ctx'" in inputs_str or '"domain_ctx"' in inputs_str
        has_global_ctx = "'global_ctx'" in inputs_str or '"global_ctx"' in inputs_str
        
        # Add if missing
        additions = []
        if not has_domain_ctx and ("'domain_ctx." in inputs_str or '"domain_ctx.' in inputs_str):
            additions.append("'domain_ctx'")
        if not has_global_ctx and ("'global_ctx." in inputs_str or '"global_ctx.' in inputs_str):
            additions.append("'global_ctx'")
        
        if additions:
            # Insert at beginning of inputs list
            new_inputs = ", ".join(additions) + ", " + inputs_str if inputs_str.strip() else ", ".join(additions)
            new_decorator = decorator_content.replace(f"inputs=[{inputs_str}]", f"inputs=[{new_inputs}]")
            return f"@process({new_decorator})"
        
        return match.group(0)
    
    new_content = re.sub(pattern, fix_decorator, content, flags=re.DOTALL)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

# Find all process files
base_path = Path(r"C:\Users\dohuy\Downloads\emotional-agent\src")
process_files = list(base_path.rglob("*processes*.py")) + list(base_path.rglob("p*.py"))

fixed_count = 0
for filepath in process_files:
    if fix_process_file(filepath):
        fixed_count += 1
        print(f"Fixed: {filepath.name}")

print(f"\nTotal fixed: {fixed_count} files")
