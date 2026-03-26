"""
Regression Tests for INC-023: Resolver Silent Deadlock Fix
===========================================================
Verifies that:
1. Missing required inputs raise ContractViolationError (not silent skip)
2. Optional inputs (required=false) skip silently
3. Inputs resolvable from context are not rejected
"""
import sys
import os
import pytest
from unittest.mock import MagicMock

# Ensure theus package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from theus.validator import AuditValidator, ContractViolationError


def _make_audit_system():
    """Create a mock AuditSystem that does nothing."""
    mock = MagicMock()
    mock.log = MagicMock()
    mock.log_fail = MagicMock()
    return mock


# ─── Test 1: Missing required input → ContractViolationError ───────────────

def test_missing_required_input_raises_error():
    """
    INC-023 Regression: validate_inputs must raise ContractViolationError
    when a field marked as required is missing from both kwargs and context.
    Previously this would silently 'continue', causing the Cognitive Freeze.
    """
    definitions = {
        "my_process": {
            "inputs": [
                {"field": "domain_ctx.fire_rate", "required": True}
            ]
        }
    }
    validator = AuditValidator(definitions, _make_audit_system())

    with pytest.raises(ContractViolationError) as exc_info:
        validator.validate_inputs("my_process", kwargs={}, context=None)

    assert "domain_ctx.fire_rate" in str(exc_info.value)
    assert "my_process" in str(exc_info.value)


# ─── Test 2: Default required=True when not specified ─────────────────────

def test_missing_unspecified_required_input_raises_error():
    """
    INC-023: If 'required' is not specified in the rule, it defaults to True.
    This ensures that new rules are strict by default.
    """
    definitions = {
        "my_process": {
            "inputs": [
                {"field": "missing_field"}  # No 'required' key — defaults to True
            ]
        }
    }
    validator = AuditValidator(definitions, _make_audit_system())

    with pytest.raises(ContractViolationError):
        validator.validate_inputs("my_process", kwargs={}, context=None)


# ─── Test 3: Optional input skips silently ────────────────────────────────

def test_optional_missing_input_is_silent():
    """
    INC-023: Optional inputs (required=False) should be silently skipped,
    preserving backward compatibility for advisory-only inputs.
    """
    definitions = {
        "my_process": {
            "inputs": [
                {"field": "optional_field", "required": False}
            ]
        }
    }
    validator = AuditValidator(definitions, _make_audit_system())

    # Should NOT raise
    validator.validate_inputs("my_process", kwargs={}, context=None)


# ─── Test 4: Input resolved from kwargs → no error ────────────────────────

def test_input_in_kwargs_passes():
    """
    INC-023: Field present in kwargs should pass validation normally.
    """
    definitions = {
        "my_process": {
            "inputs": [
                {"field": "fire_rate", "required": True, "min": 0.0, "max": 1.0}
            ]
        }
    }
    validator = AuditValidator(definitions, _make_audit_system())

    # Should NOT raise
    validator.validate_inputs("my_process", kwargs={"fire_rate": 0.5})


# ─── Test 5: Input resolved from context → no error ──────────────────────

def test_input_resolved_from_context_passes():
    """
    INC-023: If a required field is missing from kwargs but present in the
    context, it should be resolved and no error should be raised.
    This is the key new behavior introduced by the fix.
    """
    definitions = {
        "my_process": {
            "inputs": [
                {"field": "domain_ctx.fire_rate", "required": True}
            ]
        }
    }
    validator = AuditValidator(definitions, _make_audit_system())

    # Create a mock context with the field present
    mock_domain = MagicMock()
    mock_domain.fire_rate = 0.3
    mock_context = MagicMock()
    mock_context.domain_ctx = mock_domain

    # Should NOT raise — resolved from context
    validator.validate_inputs("my_process", kwargs={}, context=mock_context)


# ─── Test 6: Process with no recipe → no validation needed ───────────────

def test_process_without_recipe_skips_validation():
    """
    INC-023: Processes not registered in audit_recipe.yaml should not
    be affected by the validator (preserve existing behavior).
    """
    definitions = {}  # No recipes registered
    validator = AuditValidator(definitions, _make_audit_system())

    # Should NOT raise for any process name
    validator.validate_inputs("unregistered_process", kwargs={}, context=None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
