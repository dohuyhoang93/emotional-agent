from dataclasses import dataclass, field
from typing import List, Dict, Any
from pop import BaseGlobalContext, BaseDomainContext, BaseSystemContext

@dataclass
class GlobalContext(BaseGlobalContext):
    """Reads-only configuration and constants."""
    app_name: str = "My POP Agent"
    version: str = "0.1.0"

@dataclass
class DomainContext(BaseDomainContext):
    """Mutable domain state."""
    data: List[str] = field(default_factory=list)
    counter: int = 0

@dataclass
class SystemContext(BaseSystemContext):
    """Root container."""
    global_ctx: GlobalContext
    domain_ctx: DomainContext
    is_running: bool = True
