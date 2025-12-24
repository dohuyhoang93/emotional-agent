"""
Workflow Engine (Theus Core)
=============================
Bộ máy thực thi quy trình theo cấu hình.
"""
from typing import Callable, Dict, Any
from src.core.snn_context import SNNContext


class WorkflowEngine:
    """
    Bộ máy thực thi các Process theo thứ tự được định nghĩa.
    """
    
    def __init__(self):
        self.registry: Dict[str, Callable] = {}
    
    def register(self, name: str, process_func: Callable):
        """Đăng ký một Process vào Registry."""
        self.registry[name] = process_func
    
    def run_workflow(self, workflow_steps: list, context: SNNContext) -> SNNContext:
        """
        Thực thi một chuỗi các bước quy trình.
        
        Args:
            workflow_steps: Danh sách tên process (ví dụ: ['integrate', 'fire'])
            context: Context hiện tại
        
        Returns:
            Context sau khi đã xử lý
        """
        for step in workflow_steps:
            if step not in self.registry:
                raise ValueError(f"Process '{step}' not found in registry")
            
            process_func = self.registry[step]
            context = process_func(context)
        
        return context
    
    def run_timestep(self, workflow_steps: list, context: SNNContext) -> SNNContext:
        """
        Chạy một bước thời gian (1ms).
        """
        context = self.run_workflow(workflow_steps, context)
        context.current_time += 1
        return context
