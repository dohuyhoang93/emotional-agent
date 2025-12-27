
from theus import process

@process(inputs=[], outputs=[], side_effects=[])
def my_process(ctx):
    print("Inside Logic")

print(f"Has __wrapped__: {hasattr(my_process, '__wrapped__')}")
if hasattr(my_process, '__wrapped__'):
    my_process.__wrapped__(None)
