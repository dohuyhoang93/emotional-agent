
import os
import re

def fix_imports():
    root_dir = "src"
    
    # Replacement Rules (Order matters! Specific first)
    replacements = [
        # Contexts
        (r"from theus import BaseGlobalContext, BaseDomainContext, BaseSystemContext", 
         "from theus.context import BaseGlobalContext, BaseDomainContext, BaseSystemContext"),
        (r"from theus import BaseGlobalContext", "from theus.context import BaseGlobalContext"),
        (r"from theus import BaseDomainContext", "from theus.context import BaseDomainContext"),
        (r"from theus import BaseSystemContext", "from theus.context import BaseSystemContext"),
        
        # Engine
        (r"from theus import TheusEngine", "from theus.engine import TheusEngine"),
        
        # Contracts / Process
        (r"from theus import process", "from theus.contracts import process"),
        (r"from theus import ContractViolationError", "from theus.contracts import ContractViolationError"),
        
        # Generic mixed imports using regex if needed, but strict string replacement is safer for now.
    ]
    
    count = 0
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for file in filenames:
            if file.endswith(".py"):
                filepath = os.path.join(dirpath, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = content
                modified = False
                
                for old, new in replacements:
                    if old in new_content:
                        new_content = new_content.replace(old, new)
                        modified = True
                
                if modified:
                    print(f"Fixing imports in: {filepath}")
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    count += 1

    print(f"Fixed {count} files.")

if __name__ == "__main__":
    fix_imports()
