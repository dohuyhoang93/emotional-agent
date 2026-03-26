import asyncio
from pydantic import BaseModel, Field
import theus_core
print("Using theus_core from:", theus_core.__file__)
from theus_core.theus_core import State

class SimpleDomain(BaseModel):
    item_list: list = Field(default_factory=list)
    counter: int = 0
    async_triggered: bool = False

domain = SimpleDomain(counter=1, async_triggered=True, item_list=[])

s = State({'domain': domain})
print("Initial state data:", s.data)
print("Type of s.update:", type(s.update))

s2 = s.update(data={'domain': {'item_list': ['hello']}})


print("After update data:", s2.data)
