
import logging
from theus.audit import ContextAuditor, RuleSpec, AuditRecipe, ProcessRecipe

# Mock Context Structure using Dict
class MockContext:
    def __init__(self):
        self.tensors = {"data": [10, 20, 30]}

def test_audit_dict_access():
    """
    Verify that audit.py can now access "tensors.data"
    """
    ctx = MockContext()
    
    # Define a rule that checks tensors.data (len=3)
    # Condition: min_len 5 (Should FAIL/VIOLATE)
    
    rule = RuleSpec(
        target_field="tensors.data", # This previously failed
        condition="min_len",
        value=5,
        level="C",
        reset_on_success=True
    )
    
    recipe = AuditRecipe(
        definitions={
            "test_process": ProcessRecipe(
                process_name="test_process",
                input_rules=[rule],
                output_rules=[]
            )
        }
    )
    
    auditor = ContextAuditor(recipe)
    
    print("Running Audit on tensors.data (expecting valid check, creating violation)...")
    try:
        auditor.audit_input("test_process", ctx)
        # If we get here, getattr didn't crash.
        # We should see a violation log (level C warning).
        print("Audit executed successfully (no crash).")
        
        # Check tracker directly (white-box test)
        violations = auditor.policy.tracker.violations
        if "test_process" in violations:
            print(f"Violation recorded as expected: {violations['test_process'][0]}")
        else:
            print("ERROR: Violation NOT recorded (Logic error?)")
            
    except AttributeError as e:
        print(f"CRITICAL FAILURE: AttributeError during audit - Patch NOT working. {e}")
    except Exception as e:
        print(f"FAILURE: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_audit_dict_access()
