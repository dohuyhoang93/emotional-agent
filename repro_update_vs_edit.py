
import os
import sys
import logging
from pydantic import BaseModel, Field
from theus import TheusEngine
from theus.context import BaseSystemContext, BaseDomainContext, BaseGlobalContext

# Setup Logging
logging.basicConfig(level=logging.ERROR)

# --- Define Models ---
class NestedContent(BaseModel):
    a: int = 1
    b: int = 2

class MyDomain(BaseDomainContext):
    def __init__(self):
        self.content = NestedContent()
        self.other = "keep_me"
    
    def to_dict(self, exclude_zones=None):
        return {
            "content": self.content.model_dump(),
            "other": self.other
        }

class MySystemContext(BaseSystemContext):
    def __init__(self):
        self.global_ctx = BaseGlobalContext()
        self.domain = MyDomain()
    
    def to_dict(self):
        # Emulate standard behavior
        return {
            "domain": self.domain.to_dict(),
            "global_ctx": {}
        }

# --- Test Functions ---

def test_tx_update_behavior():
    print("\n--- TEST 1: tx.update (The Overwrite Risk) ---")
    sys_ctx = MySystemContext()
    engine = TheusEngine(sys_ctx)
    
    print(f"Initial State: {engine.state.domain.content}, other='{engine.state.domain.other}'")
    
    # User Intent: Update ONLY 'a' to 99
    # Dangerous Pattern: Passing a partial dict
    try:
        with engine.transaction() as tx:
            # Note: This dictates "Replace 'domain' with this dict"
            tx.update(data={
                "domain": {
                    "content": {"a": 99} 
                    # Missing 'b' inside content
                    # Missing 'other' inside domain
                }
            })
    except Exception as e:
        print(f"Transaction failed: {e}")

    # Check Result
    try:
        # Check 'a'
        val_a = engine.state.domain['content']['a']
        print(f"Updated 'a': {val_a}")
        
        # Check 'b' (Sibling in nested)
        try:
            val_b = engine.state.domain['content']['b']
            print(f"Sibling 'b': {val_b}")
        except KeyError:
             print("CRITICAL: Sibling 'b' is LOST/MISSING!")

        # Check 'other' (Sibling in root)
        try:
            val_other = engine.state.domain['other']
            print(f"Sibling 'other': '{val_other}'")
        except KeyError:
             print("CRITICAL: Sibling 'other' is LOST/MISSING!")
             
    except Exception as e:
        print(f"Access Error: {e}")


def test_engine_edit_behavior():
    print("\n--- TEST 2: engine.edit (The Safe Way) ---")
    sys_ctx = MySystemContext()
    engine = TheusEngine(sys_ctx)
    
    print(f"Initial State: {engine.state.domain.content}, other='{engine.state.domain.other}'")
    
    # User Intent: Update ONLY 'a' to 99
    # Safe Pattern: Mutating the object
    with engine.edit() as ctx:
        ctx.domain.content.a = 99
        # We verify that we didn't touch b or other

    # Check Result
    try:
        # Check 'a'
        val_a = getattr(engine.state.domain.content, 'a')
        print(f"Updated 'a': {val_a}")
        
        # Check 'b' (Sibling in nested)
        val_b = getattr(engine.state.domain.content, 'b')
        print(f"Sibling 'b': {val_b}")
        if val_b == 2:
            print("SUCCESS: Sibling 'b' preserved.")
        else:
            print(f"FAIL: Sibling 'b' changed to {val_b}")

        # Check 'other' (Sibling in root)
        val_other = getattr(engine.state.domain, 'other')
        print(f"Sibling 'other': '{val_other}'")
        if val_other == "keep_me":
            print("SUCCESS: Sibling 'other' preserved.")

    except Exception as e:
        print(f"Verification Failed: {e}")

def test_engine_edit_rollback():
    print("\n--- TEST 3: engine.edit Rollback Behavior ---")
    sys_ctx = MySystemContext()
    engine = TheusEngine(sys_ctx)
    
    initial_val = engine.state.domain.content.a
    print(f"Initial 'a': {initial_val}")
    
    try:
        with engine.edit() as ctx:
            ctx.domain.content.a = 555
            print(f"Inside edit, changed 'a' to: {ctx.domain.content.a}")
            raise ValueError("Simulated Failure")
    except ValueError:
        print("Caught expected error.")

    # Check Result
    final_val = engine.state.domain.content.a
    print(f"Final 'a' after exception: {final_val}")
    if final_val == initial_val:
        print("SUCCESS: engine.edit rolled back correctly.")
    else:
        print("CRITICAL: engine.edit DID NOT ROLL BACK! State is corrupted.")

if __name__ == "__main__":
    test_tx_update_behavior()
    test_engine_edit_behavior()
    test_engine_edit_rollback()
