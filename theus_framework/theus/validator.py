from typing import Any, Dict, List, Optional
import re
import logging

# [DX] Use theus.audit wrapper for consistency
from theus.audit import AuditSystem

logger = logging.getLogger(__name__)

# NOTE: Raised when a required input field is missing from both kwargs AND context.
# This replaces the silent 'continue' behavior identified in INC-023.
class ContractViolationError(Exception):
    """Raised when a @process contract is violated (missing required input)."""
    pass


class AuditValidator:
    """
    [v3.1.2] Active Policy Enforcer.
    Parses 'process_recipes' from audit_recipe.yaml and enforces rules
    via the AuditSystem (which handles Counters, Levels, and RingBuffer).

    [v3.2.0] INC-023 Fix — Strict Input Validation:
    validate_inputs now accepts an optional 'context' argument and raises
    ContractViolationError when a required input field is missing from
    BOTH kwargs and the context state. The silent 'continue' bypass is removed.
    """

    def __init__(self, definitions: Dict[str, Any], audit_system: AuditSystem):
        self.definitions = definitions or {}
        self.audit_system = audit_system

    def validate_inputs(
        self,
        func_name: str,
        kwargs: Dict[str, Any],
        context: Any = None,
    ) -> None:
        """
        Input Gate: Checks function arguments against defined rules.

        [INC-023 Fix] Now accepts an optional 'context' argument.
        If a required field is missing from kwargs, it attempts to resolve
        it from the context state before raising ContractViolationError.
        """
        recipe = self.definitions.get(func_name)
        if not recipe or "inputs" not in recipe:
            return

        input_rules = recipe["inputs"]
        for rule in input_rules:
            field = rule.get("field")
            if not field:
                continue

            # Step 1: Check in kwargs (direct pass)
            if field in kwargs:
                value = kwargs[field]
                self._check_rule(func_name, f"input:{field}", value, rule)
                continue

            # NOTE: Step 2: Field not in kwargs — try to resolve from context.
            # This is the INC-023 fix: we now look into the running context state
            # before deciding the field is missing. This handles cases where a
            # @process declares an input that is provided via Context, not directly
            # via function argument.
            if context is not None:
                ctx_val = self._resolve_from_context(context, field)
                if ctx_val is not None:
                    self._check_rule(func_name, f"input:{field}", ctx_val, rule)
                    continue

            # Step 3: Field genuinely missing — check if it's marked as required.
            # NOTE: If 'required' is not specified in the rule, we default to
            # True to enforce strict contracts. To make a field optional,
            # explicitly set required=false in the audit_recipe.yaml.
            is_required = rule.get("required", True)
            if is_required:
                msg = (
                    f"[INC-023] ContractViolationError in process '{func_name}': "
                    f"Required input field '{field}' is missing from both kwargs and context. "
                    f"This is a contract violation. Either provide the input or mark it as "
                    f"'required: false' in audit_recipe.yaml."
                )
                logger.error(msg)
                raise ContractViolationError(msg)
            else:
                # Optional field — skip silently (this is intentional)
                logger.debug(
                    f"[Validator] Optional input '{field}' missing for '{func_name}' — skipping."
                )

    def validate_outputs(self, func_name: str, pending_data: Dict[str, Any]) -> None:
        """
        Output Gate: Checks pending state mutations against defined rules.
        """
        recipe = self.definitions.get(func_name)
        if not recipe or "outputs" not in recipe:
            return

        output_rules = recipe["outputs"]
        for rule in output_rules:
            field_path = rule.get("field")
            if not field_path:
                continue

            # Resolve value from pending_data (dot notation)
            value = self._resolve_path(pending_data, field_path)
            if value is None:
                continue

            self._check_rule(func_name, f"output:{field_path}", value, rule)

    def _check_rule(self, func_name: str, key_suffix: str, value: Any, rule: Dict[str, Any]) -> None:
        """
        Core Validation Logic.
        Triggers audit_system.log_fail() on violation.
        """
        violation = None

        # 1. Numeric Checks
        if isinstance(value, (int, float)):
            if "min" in rule and value < rule["min"]:
                violation = f"Value {value} < min {rule['min']}"
            elif "max" in rule and value > rule["max"]:
                violation = f"Value {value} > max {rule['max']}"
            elif "eq" in rule and value != rule["eq"]:
                violation = f"Value {value} != {rule['eq']}"
            elif "neq" in rule and value == rule["neq"]:
                violation = f"Value {value} == {rule['neq']} (Forbidden)"

        # 2. Length Checks (Strings, Lists, Dicts)
        if hasattr(value, "__len__"):
            length = len(value)
            if "min_len" in rule and length < rule["min_len"]:
                violation = f"Length {length} < min_len {rule['min_len']}"
            elif "max_len" in rule and length > rule["max_len"]:
                violation = f"Length {length} > max_len {rule['max_len']}"

        # 3. Regex Checks (Strings)
        if isinstance(value, str) and "regex" in rule:
            pattern = rule["regex"]
            if not re.match(pattern, value):
                violation = f"Value '{value}' failed regex '{pattern}'"

        if violation:
            # Construct Audit Key: "process_name:input:field"
            audit_key = f"{func_name}:{key_suffix}"
            
            # Message
            msg = rule.get("message", violation)
            self.audit_system.log(audit_key, f"VIOLATION: {msg}")
            
            # [v3.1.3] Granular Audit Support (INC-012)
            # Map Spec string (S/A/B/C) to Rust Enum
            from theus.audit import AuditLevel
            
            level_map = {
                "S": AuditLevel.Stop,
                "A": AuditLevel.Abort,
                "B": AuditLevel.Block,
                "C": AuditLevel.Count
            }
            
            spec_level = rule.get("level")
            audit_level = level_map.get(spec_level) if spec_level else None
            
            # Threshold Override
            # Spec might use "max_threshold" or "threshold_max"
            spec_threshold = rule.get("max_threshold", rule.get("threshold_max"))
            threshold_override = int(spec_threshold) if spec_threshold is not None else None

            # Log Fail -> Increments Counter -> Check Level
            self.audit_system.log_fail(audit_key, level=audit_level, threshold_max=threshold_override)

    def _resolve_path(self, data: Dict[str, Any], path: str) -> Any:
        """Simple dot-notation resolver for nested dicts/objects."""
        parts = path.split(".")
        current = data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
            
            if current is None:
                return None
        return current

    def _resolve_from_context(self, context: Any, field: str) -> Any:
        """
        [INC-023] Resolve a dot-notation field path from the running context.
        Attempts both attribute access and dict-style access.
        Returns None if the field cannot be found.
        """
        # NOTE: Context may be a ContextGuard, SystemContext, or plain dict.
        # We try dot-notation resolution, treating the context as the root.
        parts = field.split(".")
        current = context
        for part in parts:
            if current is None:
                return None
            # Try attribute access (covers ContextGuard, dataclasses, objects)
            val = getattr(current, part, None)
            if val is None and isinstance(current, dict):
                # Try dict access as fallback
                val = current.get(part)
            current = val
        return current
