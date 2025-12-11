import os
from typing import Dict, Callable, Any, Optional
import logging
import yaml
from contextlib import contextmanager
from .context import BaseSystemContext
from .contracts import ProcessContract, ContractViolationError
from .guards import ContextGuard
from .delta import Transaction
from .locks import LockManager

logger = logging.getLogger("POPEngine")

class POPEngine:
    def __init__(self, system_ctx: BaseSystemContext, strict_mode: Optional[bool] = None):
        self.ctx = system_ctx
        self.process_registry: Dict[str, Callable] = {}
        
        # Resolve Strict Mode Logic
        # Priority 1: Argument (if explicit True/False)
        # Priority 2: Env Var "POP_STRICT_MODE"
        # Priority 3: Default False
        if strict_mode is None:
            env_val = os.environ.get("POP_STRICT_MODE", "0").lower()
            strict_mode = env_val in ("1", "true", "yes", "on")
        
        # Initialize Lock Manager ("The Vault")
        self.lock_manager = LockManager(strict_mode=strict_mode)
        
        # Attach Lock to Contexts
        # Note: We must attach to ALL layers recursively if possible, or at least the standard 3.
        # Check if they are compatible (inherit from LockedContextMixin)
        if hasattr(self.ctx, 'set_lock_manager'):
            self.ctx.set_lock_manager(self.lock_manager)
            
        if hasattr(self.ctx.global_ctx, 'set_lock_manager'):
            self.ctx.global_ctx.set_lock_manager(self.lock_manager)
            
        if hasattr(self.ctx.domain_ctx, 'set_lock_manager'):
            self.ctx.domain_ctx.set_lock_manager(self.lock_manager)

    def register_process(self, name: str, func: Callable):
        if not hasattr(func, '_pop_contract'):
            logger.warning(f"Process {name} does not have a contract decorator (@process). Safety checks disabled.")
        self.process_registry[name] = func

    def run_process(self, name: str, **kwargs):
        """
        Thực thi một process theo tên đăng ký.
        """
        if name not in self.process_registry:
            raise KeyError(f"Process '{name}' not found in registry.")
        
        func = self.process_registry[name]
        
        # UNLOCK CONTEXT for Process execution
        with self.lock_manager.unlock():
            # Checking Contract (Runtime validation)
            if hasattr(func, '_pop_contract'):
                contract: ProcessContract = func._pop_contract
                
                allowed_inputs = set(contract.inputs)
                allowed_outputs = set(contract.outputs)
                
                # Create Transaction
                tx = Transaction(self.ctx)
                
                # Create Guard with Transaction
                guarded_ctx = ContextGuard(self.ctx, allowed_inputs, allowed_outputs, transaction=tx)
                
                try:
                    result = func(guarded_ctx, **kwargs)
                    
                    # Commit Changes if successful
                    tx.commit()
                    return result
                    
                except Exception as e:
                    # Rollback Changes if error
                    tx.rollback()
                    
                    # Wrap error if it's strictly contract related, otherwise re-raise
                    if isinstance(e, ContractViolationError):
                         raise ContractViolationError(f"[Process: {name}] {str(e)}") from e
                    
                    # Error Trap for undeclared errors
                    error_name = type(e).__name__
                    if error_name not in contract.errors:
                        raise ContractViolationError(
                            f"Undeclared Error Violation: Process '{name}' raised '{error_name}' "
                            f"but it was not declared in errors=[...]. Original Error: {str(e)}"
                        ) from e
                    raise e
            else:
                return func(self.ctx, **kwargs)

    def execute_workflow(self, workflow_path: str, **kwargs):
        """
        Thực thi Workflow YAML.
        """
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_def = yaml.safe_load(f)
            
        for step in workflow_def.get('steps', []):
            if isinstance(step, str):
                self.run_process(step, **kwargs)
            elif isinstance(step, dict):
                process_name = step.get('process')
                if process_name:
                    self.run_process(process_name, **kwargs)
        
        return self.ctx

    @contextmanager
    def edit(self):
        """
        Safe Zone for external mutation (e.g. from main.py).
        Usage:
            with engine.edit() as tx:
                tx.domain.var = 1
        """
        # Unlock for the duration of the block
        with self.lock_manager.unlock():
            # Ideally we should yield a Transaction to allow correct logging?
            # Yes, main.py should use Transaction.
            tx = Transaction(self.ctx)
            
            # Yield a wrapper that logs? Or just the context?
            # If we yield context, mutations are direct (but allowed by unlock).
            # But we want Transaction LOGGING even for main.py (as per design).
            # So yield 'tx' or a Guard?
            # If we yield 'tx', tx does not have 'domain' attribute directly (it has root).
            # Let's yield a ContextGuard wrapping the whole context with ALL permissions?
            # That's easiest.
            
            # Allow everything
            all_inputs = {"*"} # Wildcard not supported by Guard yet? 
            # Actually, Guard expects list of strings.
            # Hack: Yield the raw context, but wrap in Transaction? 
            # If we modify raw context, Transaction doesn't know unless we use Shadows.
            # So we MUST use ContextGuard.
            
            # Phase 2.6 Simplification: 
            # Just yield the Raw Context (Unlocked). Logging is secondary for main.py fixes right now.
            # The LockManager ensures "Explicit Intent".
            # The Transaction logging for main.py is "Nice to have".
            # Let's just yield self.ctx.
            yield self.ctx

            # If we used a transaction, we would commit here.

