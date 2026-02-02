
from theus import process
from theus.contracts import SemanticType
from theus.structures import StateUpdate

@process(outputs=['domain.counter'])
async def async_inc(ctx):
    ctx.domain.counter += 1
    return ctx.domain.counter

@process(outputs=['domain.counter'])
def sync_inc(ctx):
    ctx.domain.counter += 1
    return ctx.domain.counter

@process(outputs=['domain.items'], parallel=True)
def parallel_append(ctx):
    # Parallel processes must return the change they want to apply
    item = ctx.input.get('item')
    return StateUpdate(key='domain.items', val=[item]) # Simple overwrite for test

@process(semantic=SemanticType.PURE, outputs=['domain.counter'])
def pure_violation(ctx):
    ctx.domain.counter = 999
    return "Violated"

@process(outputs=['domain.counter'], errors=["SimulatedError"])
def test_errors_metadata(ctx):
    raise ValueError("RealError")
