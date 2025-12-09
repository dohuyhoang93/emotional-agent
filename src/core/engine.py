from typing import List, Callable, Dict, Any, Optional
import functools
import logging
import inspect
import yaml
from .context import SystemContext, GlobalContext, DomainContext

logger = logging.getLogger("POP_Engine")

class ProcessContract:
    def __init__(self, inputs: List[str], outputs: List[str], side_effects: List[str] = None, errors: List[str] = None):
        self.inputs = inputs
        self.outputs = outputs
        self.side_effects = side_effects or []
        self.errors = errors or []

def process(inputs: List[str], outputs: List[str], side_effects: List[str] = None, errors: List[str] = None):
    """
    Decorator để định nghĩa một POP Process với I/O Contract rõ ràng.
    Tuân thủ POP Manifesto Chapter 10.
    """
    def decorator(func: Callable):
        func._pop_contract = ProcessContract(inputs, outputs, side_effects, errors)
        
        # Pre-compute signature parameters
        sig = inspect.signature(func)
        valid_params = set(sig.parameters.keys())
        
        @functools.wraps(func)
        def wrapper(system_ctx: SystemContext, *args, **kwargs):
            # 1. Validation Logic
            
            # 2. Filter kwargs to only pass what the function accepts
            # We assume system_ctx is always the first arg (or 'ctx')
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
            
            # If func accepts **kwargs, pass all
            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
                filtered_kwargs = kwargs
            
            return func(system_ctx, *args, **filtered_kwargs)
        return wrapper
    return decorator

class POPEngine:
    def __init__(self, system_ctx: SystemContext):
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
        
        # Checking Contract (Runtime validation placeholder)
        if hasattr(func, '_pop_contract'):
            contract: ProcessContract = func._pop_contract
            # logger.debug(f"Executing {name}. Inputs: {contract.inputs}, Outputs: {contract.outputs}")
            pass
        
        # Execute
        result = func(self.ctx, **kwargs)
        return result

    def execute_workflow(self, workflow_path: str, **kwargs):
        """
        Thực thi một Workflow được định nghĩa trong file YAML.
        """
        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_def = yaml.safe_load(f)
            
        # logger.info(f"Starting Workflow: {workflow_def.get('name', 'Unknown')}")
        
        for step in workflow_def.get('steps', []):
            if isinstance(step, str):
                self.run_process(step, **kwargs)
            elif isinstance(step, dict):
                process_name = step.get('process')
                if process_name:
                    self.run_process(process_name, **kwargs)
        
        return self.ctx

    def get_domain(self) -> DomainContext:
        return self.ctx.domain_ctx

    def get_global(self) -> GlobalContext:
        return self.ctx.global_ctx
