from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Any
from theus.context import BaseSystemContext

# --- 1. Global (Configuration) ---
class DemoGlobal(BaseModel):
    app_name: str = "Theus V3 Demo App"
    version: str = "3.0.1"
    max_retries: int = 3

# --- 2. Domain (Mutable State) ---
class DemoDomain(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # State flags
    status: str = "IDLE"          # System Status
    processed_count: int = 0      # Logic Counter
    items: List[str] = Field(default_factory=list) # Data Queue
    
    # E-Commerce Example
    order_request: Optional[dict] = None
    orders: List[dict] = Field(default_factory=list)
    balance: float = 0.0
    processed_orders: List[str] = Field(default_factory=list)

    # Smart Agent Example
    sensor_data: dict = Field(default_factory=dict)
    action: str = "IDLE"
    action_log: List[str] = Field(default_factory=list)

    # Signals Example
    signal_count: int = 0
    received_signals: List[str] = Field(default_factory=list)
    notified: bool = False

    # Error tracking (META Zone)
    meta_last_error: Optional[str] = None

# --- 3. System (Root Container) ---
class DemoSystemContext(BaseSystemContext):
    def __init__(self):
        self.global_ctx = DemoGlobal()
        self.domain_ctx = DemoDomain()
