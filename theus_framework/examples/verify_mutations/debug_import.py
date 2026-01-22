import sys
import os

print("--- DEBUG IMPORT ---")
print(f"CWD: {os.getcwd()}")
print("SYS.PATH:")
for p in sys.path:
    print(f"  {p}")

try:
    from theus_core import TheusEngine
    print(f"SUCCESS: Imported TheusEngine")
    print("\nTheusEngine methods:")
    for m in dir(TheusEngine):
        print(f"  {m}")
    
    # Try instantiation test
    try:
        e = TheusEngine()
        print("Instantiation: TheusEngine() OK")
    except Exception as ex:
        print(f"Instantiation: TheusEngine() FAILED: {ex}")

except ImportError as e:
    print(f"FAIL: {e}")
    
    # List site-packages content
    site_packages = [p for p in sys.path if "site-packages" in p]
    if site_packages:
        sp = site_packages[0] # Usually first one
        print(f"\nListing {sp}:")
        try:
             files = os.listdir(sp)
             for f in files:
                 if "theus" in f:
                     print(f"  {f}")
        except:
            print("  Cannot listing")
