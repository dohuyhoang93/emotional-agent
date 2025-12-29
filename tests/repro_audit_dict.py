
class MockContext:
    def __init__(self):
        self.tensors = {"data": [1, 2, 3]}

def resolve(ctx, path):
    parts = path.split('.')
    current = ctx
    for p in parts:
        print(f"Resolving {p} on {type(current)}")
        current = getattr(current, p)
    return current

try:
    c = MockContext()
    # This mimics accessing "tensors.data" where tensors is a dict
    resolve(c, "tensors.data")
except Exception as e:
    print(f"Failed: {e}")
