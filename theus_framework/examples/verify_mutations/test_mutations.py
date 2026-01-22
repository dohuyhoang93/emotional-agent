import sys
import os
import asyncio
from dataclasses import dataclass, field
from typing import List

# Fix Path - REMOVED to test INSTALLED package
# sys.path.insert(0, os.path.abspath("../../"))

from theus import TheusEngine
from theus.context import BaseSystemContext, BaseDomainContext, BaseGlobalContext
from theus.contracts import process, SemanticType

# --- 1. Context Definition (Chapter 02) ---
@dataclass
class VerifyDomain(BaseDomainContext):
    counter: int = 0
    history: List[str] = field(default_factory=list)

@dataclass
class VerifyContext(BaseSystemContext):
    domain: VerifyDomain = field(default_factory=VerifyDomain)
    global_ctx: BaseGlobalContext = field(default_factory=BaseGlobalContext)

# --- 2. Processes (Chapter 03: Implicit POP) ---

@process(
    inputs=['domain.counter', 'domain.history'],
    outputs=['domain.counter', 'domain.history'],
    semantic=SemanticType.EFFECT
)
def increment_process(ctx, amount: int):
    """
    Standard POP Process.
    Uses Copy-on-Write pattern.
    """
    # 1. Read Frozen (Theus v3 returns Dict/FrozenDict from Rust)
    # NOTE: Rust Core stores state as Dict. Attribute access requires Object hydration which is optional.
    # We use Dict access for raw speed/safety as per Ch 3.
    # 1. Read Frozen (Theus v3 returns Dict/FrozenDict from Rust)
    # NOTE: Rust Core stores state as Dict. Attribute access requires Object hydration which is optional.
    # We use Dict access for raw speed/safety as per Ch 3.
    count = ctx.domain['counter']
    hist = list(ctx.domain['history']) # Copy!
    
    # 2. Mutate Local
    new_count = count + amount
    hist.append(f"Incremented by {amount}. New total: {new_count}")
    
    # 3. Return (Engine handles Transaction)
    return new_count, hist

@process(
    inputs=['domain.history'],
    outputs=['domain.history']
)
def clean_history_process(ctx):
    """Simple list clear."""
    return []

async def run_verification():
    print("=== [STATE MUTATION VERIFICATION] ===")
    
    # 1. Setup
    dom = VerifyDomain()
    # 1. Setup
    dom = VerifyDomain()
    sys_ctx = VerifyContext(domain=dom)
    engine = TheusEngine(sys_ctx, strict_mode=True)
    engine = TheusEngine(sys_ctx, strict_mode=True)
    
    engine.register(increment_process)
    engine.register(clean_history_process)
    
    print("\n--- TEST 1: Batch Transaction (Init) ---")
    # SCENARIO: Initializing data safely
    try:
        with engine.transaction() as tx:
            tx.update(data={
                "domain": {
                    "counter": 100, 
                    "history": ["Init: 100"]
                }
            })
        print("✅ Batch Transaction: Success")
        
        # Verify
        current = engine.state.domain.counter
        print(f"   Value: {current} (Expected: 100)")
        if current != 100: raise AssertionError("Batch Init Failed")
            
    except Exception as e:
        print(f"❌ Batch Transaction Failed: {e}")
        return

    print("\n--- TEST 2: Implicit POP (@process) ---")
    # SCENARIO: Normal Business Logic
    try:
        await engine.execute(increment_process, amount=50)
        print("✅ Implicit Process: Success")
        
        # Verify
        current = engine.state.domain.counter
        hist = engine.state.domain.history
        print(f"   Value: {current} (Expected: 150)")
        print(f"   History: {hist}")
        
        if current != 150: raise AssertionError("Implicit POP Failed")
        
    except Exception as e:
        print(f"❌ Implicit POP Failed: {e}")
        return

    print("\n--- TEST 3: Explicit CAS (Advanced) ---")
    # SCENARIO: Manual atomic update (The Scalpel)
    try:
        # A. Failure Case (Wrong Version)
        bad_ver = 99999
        res = engine.compare_and_swap(bad_ver, {"domain": {"counter": 999}})
        print(f"DEBUG: CAS(BadVer) returned type: {type(res)} Val: {res}")
        
        # If it returns a result instead of raising, check if it implies failure
        # In Theus v3, CAS might return a Conflict Struct if not strict?
        # But we set strict_mode=True.
        # Check safely.
        if hasattr(res, "should_retry") or res is False:
             print("✅ CAS Safety: Rejected (Conflict Detected via Return)")
        elif res is None:
             # Void return usually means success in PyO3 if no error raised?
             # But if it succeeded with bad version, that is a BUG.
             # Verify state didn't change.
             if engine.state.domain.counter != 999:
                 print("✅ CAS Safety: Rejected (State Unchanged)")
             else:
                 print("❌ CAS Safety: FAILED (State Mutated illegally!)")
        else:
             print(f"⚠️ CAS Safety: Unknown Return. Assumed Rejected if state safe.")

        # B. Success Case (Read-Modify-Write)
        current_ver = engine.state.version
        print(f"   Capturing Version: {current_ver}")
        
        # Manual update - Preserve History! (Deep Merge)
        # 1. Get current domain dict
        curr_domain = engine.state.domain.copy() # Shallow copy of FrozenDict
        # 2. Update
        curr_domain['counter'] = 200
        
        # 3. Write
        engine.compare_and_swap(current_ver, {"domain": curr_domain})
        
        # Verify State
        if engine.state.domain.counter == 200:
             print("✅ CAS Valid Update: Success (State Verified)")
             print(f"   History Check: {engine.state.domain.history}") # Should be present
        else:
             print("❌ CAS Valid Update Failed: State did not change!")

    except Exception as e:
        print(f"❌ Explicit CAS Error: {e}")

    print("\n=== VERIFICATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_verification())
