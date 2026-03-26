from pydantic import BaseModel, Field
class SimpleDomain(BaseModel):
    item_list: list = Field(default_factory=list)
    counter: int = 0
    async_triggered: bool = False
d = SimpleDomain()
print(f"Type: {type(d)}")
print(f"Has model_dump: {hasattr(d, 'model_dump')}")
print(f"Has dict: {hasattr(d, 'dict')}")
print(f"Has __dict__: {hasattr(d, '__dict__')}")
print(f"Result: {d.model_dump()}")
