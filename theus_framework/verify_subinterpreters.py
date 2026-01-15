import sys
print(f"Python Version: {sys.version}")

try:
    import _xxsubinterpreters as interpreters
    print("✅ _xxsubinterpreters module found.")
    try:
        if hasattr(interpreters, 'run'):
            print("   Has 'run' function.")
        if hasattr(interpreters, 'create'):
            print("   Has 'create' function.")
    except Exception as e:
        print(f"Error inspecting module: {e}")
except ImportError:
    print("❌ _xxsubinterpreters module NOT found.")

try:
    import interpreters
    print("✅ 'interpreters' (PEP 554) module found.")
except ImportError:
    print("❌ 'interpreters' (PEP 554) module NOT found.")
