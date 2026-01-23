"""
TEST SUPERVISOR SECURITY
========================
Verifies that the SupervisorProxy correctly intercepts and blocks writes
based on the Engine's security policy.
"""
import sys
import os
sys.path.insert(0, os.path.abspath("."))

from theus.prototype.supervisor import SupervisorEngine

class UserData:
    def __init__(self, name):
        self.name = name
        self.secret = "hidden"

def test_security():
    print("--- [Security Test] Supervisor Gatekeeper ---")
    
    data = UserData("Alice")
    engine = SupervisorEngine(init_data={
        "user_profile": data,      # Authorized (default policy)
        "system_config": data      # Unauthorized (starts with 'system')
    })
    
    # 1. Test Authorized Write
    print("1. Testing Authorized Write (user_profile)...")
    proxy = engine.read("user_profile")
    try:
        proxy.name = "Bob" # Should succeed
        print(f"   ✅ Success! Name changed to: {proxy.name}")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        
    # 2. Test Unauthorized Write
    print("2. Testing Unauthorized Write (system_config)...")
    sys_proxy = engine.read("system_config")
    try:
        sys_proxy.name = "Hacked" # Should FAIL
        print("   ❌ FAILED: Security check bypassed!")
    except PermissionError as e:
        print(f"   ✅ BLOCKED: Caught expected error: {e}")
    except Exception as e:
        print(f"   ❓ Unexpected Error: {e}")

    print("\n--- Security Test Complete ---")

if __name__ == "__main__":
    test_security()
