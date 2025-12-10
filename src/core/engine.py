import logging
# Import from Independent SDK
import sys
import os
sdk_path = os.path.join(os.getcwd(), 'python_pop_sdk')
if sdk_path not in sys.path:
    sys.path.append(sdk_path)

from pop import POPEngine as BasePOPEngine, process, ContractViolationError

# Re-export key components so existing code doesn't break
ContractViolationError = ContractViolationError
process = process

class POPEngine(BasePOPEngine):
    """
    Wrapper của POPEngine từ SDK.
    Có thể thêm logic custom của dự án ở đây nếu cần (như logging đặc thù).
    Nhưng hiện tại nó chỉ kế thừa.
    """
    def get_domain(self):
        return self.ctx.domain_ctx
        
    def get_global(self):
        return self.ctx.global_ctx
