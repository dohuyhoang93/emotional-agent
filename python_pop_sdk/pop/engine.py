from typing import Dict, Callable, Any
import logging
import yaml
from .context import BaseSystemContext
from .contracts import ProcessContract, ContractViolationError
from .guards import ContextGuard
from .delta import Transaction

logger = logging.getLogger("POPEngine")

class POPEngine:
    def __init__(self, system_ctx: BaseSystemContext):
        self.ctx = system_ctx
        self.process_registry: Dict[str, Callable] = {}

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
