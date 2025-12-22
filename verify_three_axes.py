from typing import Set, Any
from dataclasses import dataclass
import logging

# Mocking the imports if running in standalone mode where 'theus' might not be in path
# But we are in the environment, so we should try to import directly.
try:
    from theus.guards import ContextGuard
    from theus.contracts import ContractViolationError
    from theus.zones import resolve_zone, ContextZone
except ImportError:
    # If explicit path import is needed we might need to adjust sys.path
    import sys
    import os
    sys.path.append(os.path.join(os.getcwd(), 'theus'))
    from theus.guards import ContextGuard
    from theus.contracts import ContractViolationError
    from theus.zones import resolve_zone, ContextZone

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VERIFY")

@dataclass
class MockDomainContext:
    user_id: int = 100
    balance: float = 500.0
    sig_stop: bool = False
    cmd_reset: bool = False
    meta_trace: str = "init_trace"

def test_zone_policy_enforcement():
    print("\n--- TEST 1: Zone Policy Enforcement (Input Dependencies) ---")
    data_ctx = MockDomainContext()
    
    # CASE 1: declaring a Signal as Input should Trigger Warning/Error
    print("[1.1] Attempting to declare inputs=['sig_stop'] (Expect Violation)")
    try:
        # strict_mode=True to force exception
        guard = ContextGuard(data_ctx, allowed_inputs={'sig_stop'}, allowed_outputs=set(), strict_mode=True)
        print("FAILED: ContextGuard allowed 'sig_stop' as input in Strict Mode!")
    except ContractViolationError as e:
        print(f"PASSED: Caught expected violation: {e}")
    except Exception as e:
        print(f"FAILED: Caught unexpected exception: {e}")

    # CASE 2: declaring Data as Input (Normal)
    print("[1.2] Attempting to declare inputs=['user_id'] (Expect Success)")
    try:
        guard = ContextGuard(data_ctx, allowed_inputs={'user_id'}, allowed_outputs=set(), strict_mode=True)
        print("PASSED: ContextGuard allowed 'user_id' as input.")
    except Exception as e:
        print(f"FAILED: Unexpected error for valid input: {e}")

def test_semantic_enforcement():
    print("\n--- TEST 2: Semantic Enforcement (Read/Write Contracts) ---")
    data_ctx = MockDomainContext()
    
    # Guard setup: Input = user_id (Read-only), Output = balance (Write-only? No, usually Read-Write behavior depends on implementation)
    # Check guard implementation:
    # READ GUARD: Must be in allowed_inputs to READ.
    # WRITE GUARD: Must be in allowed_outputs to WRITE.
    
    guard = ContextGuard(
        data_ctx, 
        allowed_inputs={'user_id', 'balance'}, 
        allowed_outputs={'balance'}, 
        strict_mode=True
    )
    
    # CASE 1: Read Allowed Input
    print("[2.1] Reading 'user_id' (Expect Success)")
    try:
        val = guard.user_id
        print(f"PASSED: Read user_id = {val}")
    except Exception as e:
        print(f"FAILED: Could not read allowed input: {e}")
        
    # CASE 2: Write to Read-Only Input
    print("[2.2] Writing to 'user_id' (Expect Fail - Illegal Write)")
    try:
        guard.user_id = 999
        print("FAILED: ContextGuard allowed writing to read-only 'user_id'!")
    except ContractViolationError as e:
        print(f"PASSED: Caught expected violation: {e}")
        
    # CASE 3: Write to Allowed Output
    print("[2.3] Writing to 'balance' (Expect Success)")
    try:
        guard.balance = 1000.0
        print(f"PASSED: Wrote balance = 1000.0")
        # Verify underlying object (assuming simplified transaction logic in guard for this test)
        # Note: If transaction is None, guard writes directly to target_obj (based on code reading)
        if data_ctx.balance == 1000.0:
             print("PASSED: Underlying object updated.")
        else:
             print(f"WARNING: Underlying object not updated? {data_ctx.balance}")
             
    except Exception as e:
        print(f"FAILED: Could not write to allowed output: {e}")

    # CASE 4: Read Undecided Variable
    print("[2.4] Reading 'sig_stop' (Not in input) (Expect Fail - Illegal Read)")
    try:
        val = guard.sig_stop
        print("FAILED: ContextGuard allowed reading undeclared 'sig_stop'!")
    except ContractViolationError as e:
        print(f"PASSED: Caught expected violation: {e}")

def test_zone_resolution():
    print("\n--- TEST 3: Zone Resolution Logic ---")
    
    cases = [
        ("user_id", ContextZone.DATA),
        ("sig_stop", ContextZone.SIGNAL),
        ("cmd_reset", ContextZone.SIGNAL),
        ("meta_trace", ContextZone.META),
        ("signal_fake", ContextZone.DATA), # 'signal' prefix is not 'sig_'
        ("my_data", ContextZone.DATA)
    ]
    
    for key, expected in cases:
        actual = resolve_zone(key)
        status = "PASSED" if actual == expected else "FAILED"
        print(f"[{status}] Key: '{key:<15}' Expected: {expected.value:<10} Actual: {actual.value}")

if __name__ == "__main__":
    test_zone_resolution()
    test_zone_policy_enforcement()
    test_semantic_enforcement()
