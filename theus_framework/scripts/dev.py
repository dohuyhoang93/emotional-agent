import subprocess
import sys
import os
import platform

def run(cmd, env=None):
    """Run a command in a cross-platform way."""
    print(f"Example: {' '.join(cmd)}")
    
    # On Windows, shell=True is often needed for identifying executables in PATH if they are scripts/shims
    use_shell = (platform.system() == "Windows")
    
    try:
        subprocess.check_call(cmd, env=env, shell=use_shell)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error executing: {' '.join(cmd)}")
        sys.exit(e.returncode)

def cmd_build():
    print("\n🔨 [1/2] Building Rust Core (Maturin Develop)...")
    
    # [Fix] maturin develop needs VIRTUAL_ENV set to know where to install.
    # If not set, infer from the current running python executable.
    env = os.environ.copy()
    # [Fix] Explicitly tell PyO3 which python to link against.
    # This solves 'error: no Python 3.x interpreter found' on Windows.
    env["PYO3_PYTHON"] = sys.executable
    # [Fix] Support Python 3.14 (Preview) via Forward Compatibility
    env["PYO3_USE_ABI3_FORWARD_COMPATIBILITY"] = "1"

    if "VIRTUAL_ENV" not in env:
        # Assuming sys.executable is inside the venv (e.g. .venv/Scripts/python.exe)
        # We need the root of the venv.
        # Window: venv/Scripts/python.exe -> venv
        # Linux: venv/bin/python -> venv
        python_dir = os.path.dirname(sys.executable)
        venv_root = os.path.dirname(python_dir)
        
        # Simple heuristic check: does pyvenv.cfg exist?
        if os.path.exists(os.path.join(venv_root, "pyvenv.cfg")):
            print(f"   ℹ️  Auto-detected VIRTUAL_ENV: {venv_root}")
            env["VIRTUAL_ENV"] = venv_root
            # Also update PATH to prioritize this venv's scripts (where maturin might be)
            env["PATH"] = python_dir + os.pathsep + env.get("PATH", "")
        else:
             print("   ⚠️  Warning: specific VIRTUAL_ENV not detected. Maturin might fail if not in a venv.")

    # Try running 'maturin' directly.
    try:
        run(["maturin", "develop"], env=env)
    except SystemExit:
        print("\n⚠️ 'maturin develop' failed (likely due to System Python usage).")
        print("🔄 Falling back to 'pip install .' (Standard Install)...")
        # Use simple pip install
        run([sys.executable, "-m", "pip", "install", "."], env=env)
    
    print("\n📝 [2/2] Generating Python Type Stubs...")
    env["PYTHONPATH"] = os.getcwd()
    run([sys.executable, "scripts/gen_stubs.py"], env=env)
    
    print("✅ Build Complete.")

def cmd_verify():
    print("\n🛡️ Verifying API Parity (Defense Layer)...")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    run([sys.executable, "tests/verify_api_parity.py"], env=env)
    print("✅ Parity Check Passed.")

def print_help():
    print("Theus Cross-Platform Dev Tool")
    print("Usage: python scripts/dev.py <command>")
    print("Commands:")
    print("  build   : Compile Rust & Generate Stubs")
    print("  verify  : Run API Parity Check")
    print("  all     : Build + Verify")

def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "build":
        cmd_build()
    elif command == "verify":
        cmd_verify()
    elif command == "all":
        cmd_build()
        cmd_verify()
    else:
        print(f"Unknown command: {command}")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
