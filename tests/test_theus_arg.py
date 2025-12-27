
from theus import process

try:
    @process(inputs=[], outputs=[], side_effects=[], transactional=False)
    def my_process(ctx):
        pass
    print("transactional=False is SUPPORTED")
except TypeError as e:
    print(f"transactional=False is NOT SUPPORTED: {e}")
except Exception as e:
    print(f"Other Error: {e}")
