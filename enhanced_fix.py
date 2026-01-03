"""
Enhanced fix script that handles ALL edge cases
"""
import re
from pathlib import Path

def comprehensive_fix_v2(filepath):
    """Fix with better pattern matching"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        return False
    
    original = content
    
    # Find all @process decorators with more robust pattern
    # Match @process( ... ) including multi-line with nested parentheses
    pattern = r'@process\s*\([^)]*(?:\([^)]*\)[^)]*)*\)'
    
    def fix_decorator(match):
        decorator = match.group(0)
        
        # Fix inputs
        inputs_pattern = r"inputs\s*=\s*\[(.*?)\]"
        inputs_match = re.search(inputs_pattern, decorator, re.DOTALL)
        
        if inputs_match:
            inputs_content = inputs_match.group(1)
            
            # Check for domain_ctx children
            if re.search(r"['\"]domain_ctx\.", inputs_content):
                if not re.search(r"['\"]domain_ctx['\"](?!\.)

", inputs_content):
                    # Add at start
                    new_inputs = "'domain_ctx', " + inputs_content
                    decorator = decorator.replace(
                        f"inputs=[{inputs_content}]",
                        f"inputs=[{new_inputs}]"
                    )
            
            # Re-extract after potential modification
            inputs_match = re.search(inputs_pattern, decorator, re.DOTALL)
            if inputs_match:
                inputs_content = inputs_match.group(1)
                
                # Check for global_ctx children
                if re.search(r"['\"]global_ctx\.", inputs_content):
                    if not re.search(r"['\"]global_ctx['\"](?!\.)", inputs_content):
                        new_inputs = "'global_ctx', " + inputs_content
                        decorator = decorator.replace(
                            f"inputs=[{inputs_content}]",
                            f"inputs=[{new_inputs}]"
                        )
        
        # Fix outputs
        outputs_pattern = r"outputs\s*=\s*\[(.*?)\]"
        outputs_match = re.search(outputs_pattern, decorator, re.DOTALL)
        
        if outputs_match:
            outputs_content = outputs_match.group(1)
            
            # Check for domain_ctx or domain children
            if re.search(r"['\"]domain_ctx\.", outputs_content) or re.search(r"['\"]domain\.", outputs_content):
                if not re.search(r"['\"]domain_ctx['\"](?!\.)", outputs_content):
                    new_outputs = "'domain_ctx', " + outputs_content
                    decorator = decorator.replace(
                        f"outputs=[{outputs_content}]",
                        f"outputs=[{new_outputs}]"
                    )
            
            # Re-extract
            outputs_match = re.search(outputs_pattern, decorator, re.DOTALL)
            if outputs_match:
                outputs_content = outputs_match.group(1)
                
                if re.search(r"['\"]global_ctx\.", outputs_content) or re.search(r"['\"]global\.", outputs_content):
                    if not re.search(r"['\"]global_ctx['\"](?!\.)", outputs_content):
                        new_outputs = "'global_ctx', " + outputs_content
                        decorator = decorator.replace(
                            f"outputs=[{outputs_content}]",
                            f"outputs=[{new_outputs}]"
                        )
        
        return decorator
    
    content = re.sub(pattern, fix_decorator, content, flags=re.DOTALL)
    
    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Process ALL Python files
base = Path(r"C:\Users\dohuy\Downloads\emotional-agent\src")
all_files = list(base.rglob("*.py"))

fixed = 0
for f in all_files:
    if comprehensive_fix_v2(f):
        print(f"Fixed: {f.relative_to(base)}")
        fixed += 1

print(f"\n✅ Total: {fixed} files")
