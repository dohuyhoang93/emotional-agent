import pytest
from theus.audit import AuditSystem, AuditRecipe, AuditBlockError

# TDD: Audit Logic

def test_audit_thresholds_accumulate():
    recipe = AuditRecipe(threshold_max=3)
    audit = AuditSystem(recipe)
    
    # 3 fails -> OK (Warning)
    audit.log_fail("p1")
    audit.log_fail("p1")
    audit.log_fail("p1")
    assert audit.get_count("p1") == 3
    
    # 4th fail -> BLOCK
    with pytest.raises(AuditBlockError):
        audit.log_fail("p1")

def test_audit_reset_on_success():
    recipe = AuditRecipe(threshold_max=3, reset_on_success=True)
    audit = AuditSystem(recipe)
    
    audit.log_fail("p1")
    audit.log_fail("p1")
    assert audit.get_count("p1") == 2
    
    audit.log_success("p1")
    assert audit.get_count("p1") == 0 # Reset!
