import os
import sys

if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

from src.orchestrator.context import OrchestratorDomainContext
ctx = OrchestratorDomainContext()
keys = list(ctx.__dict__.keys())

print("DATACLASS KEYS:", keys)
