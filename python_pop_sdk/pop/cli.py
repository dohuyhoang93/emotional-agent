import argparse
import os
import sys
from pathlib import Path
from .templates import (
    TEMPLATE_ENV, 
    TEMPLATE_MAIN, 
    TEMPLATE_CONTEXT, 
    TEMPLATE_WORKFLOW, 
    TEMPLATE_Hello_PROCESS
)

def init_project(project_name: str, target_dir: Path):
    """
    Scaffolds a new POP project.
    """
    print(f"🚀 Initializing POP Project: {project_name}")
    
    # 1. Create Directories
    try:
        (target_dir / "src" / "processes").mkdir(parents=True, exist_ok=True)
        (target_dir / "workflows").mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"❌ Error creating directories: {e}")
        sys.exit(1)

    # 2. Write Files
    files_to_create = {
        ".env": TEMPLATE_ENV,
        "main.py": TEMPLATE_MAIN,
        "src/context.py": TEMPLATE_CONTEXT,
        "src/__init__.py": "",
        "src/processes/__init__.py": "",
        "src/processes/p_hello.py": TEMPLATE_Hello_PROCESS,
        "workflows/main_workflow.yaml": TEMPLATE_WORKFLOW
    }

    for rel_path, content in files_to_create.items():
        file_path = target_dir / rel_path
        if file_path.exists():
            print(f"   ⚠️  Skipping existing file: {rel_path}")
            continue
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"   ✅ Created {rel_path}")

    print("\n🎉 Project created successfully!")
    print("\nNext steps:")
    if project_name != ".":
        print(f"  cd {project_name}")
    print("  pip install -r requirements.txt (if you have one)")
    print("  python main.py")

def main():
    parser = argparse.ArgumentParser(description="POP SDK CLI - Manage your Process-Oriented projects.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: init
    parser_init = subparsers.add_parser("init", help="Initialize a new POP project.")
    parser_init.add_argument("name", help="Name of the project (or '.' for current directory).")

    args = parser.parse_args()

    if args.command == "init":
        project_name = args.name
        
        if project_name == ".":
            target_path = Path.cwd()
            project_name = target_path.name
        else:
            target_path = Path.cwd() / project_name
            if target_path.exists() and any(target_path.iterdir()):
                print(f"❌ Directory '{project_name}' exists and is not empty.")
                sys.exit(1)
            target_path.mkdir(exist_ok=True)
            
        init_project(project_name, target_path)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
