
from theus import process

@process(
    inputs=['domain_ctx'],
    outputs=['domain_ctx']
)
def noop_process(context):
    context.domain_ctx.counter += 1
    return context
