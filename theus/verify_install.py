
import sys
try:
    import theus_core
    print("✅ SUCCESS: theus_core imported successfully!")
    print(f"File: {theus_core.__file__}")
    print(f"Contents: {dir(theus_core)}")
except ImportError as e:
    print(f"❌ FAILURE: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")
    sys.exit(1)
