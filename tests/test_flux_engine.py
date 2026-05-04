
import unittest
from dataclasses import dataclass
from typing import Any
from theus.engine import TheusEngine
from theus.contracts import process

@dataclass
class TestDomainContext:
    counter: int = 0
    flag: bool = False
    
@dataclass
class TestSystemContext:
    domain_ctx: TestDomainContext
    global_ctx: Any = None # Added for compatibility

@process(inputs=['domain_ctx'], outputs=['domain_ctx'])    
def p_increment(ctx):
    ctx.domain_ctx.counter += 1
    
@process(inputs=['domain_ctx'], outputs=['domain_ctx'])
def p_set_flag_true(ctx):
    ctx.domain_ctx.flag = True

@process(inputs=['domain_ctx'], outputs=['domain_ctx'])    
def p_reset_counter(ctx):
    ctx.domain_ctx.counter = 0

class TestFluxEngine(unittest.TestCase):
    def setUp(self):
        self.domain = TestDomainContext()
        self.sys = TestSystemContext(domain_ctx=self.domain)
        # Engine is available for registration tests; processes are called directly
        self.engine = TheusEngine(self.sys, strict_guards=False)
        self.engine.register(p_increment)
        self.engine.register(p_set_flag_true)
        self.engine.register(p_reset_counter)

    def test_flux_run_simple(self):
        p_increment(self.sys)
        p_increment(self.sys)
        self.assertEqual(self.domain.counter, 2)

    def test_flux_if(self):
        self.domain.counter = 5
        # Simulate: if domain.counter > 3: set_flag else: increment
        if self.domain.counter > 3:
            p_set_flag_true(self.sys)
        else:
            p_increment(self.sys)
        self.assertTrue(self.domain.flag)
        self.assertEqual(self.domain.counter, 5) # Not incremented

    def test_flux_if_else(self):
        self.domain.counter = 1
        # Simulate: if domain.counter > 3: set_flag else: increment
        if self.domain.counter > 3:
            p_set_flag_true(self.sys)
        else:
            p_increment(self.sys)
        self.assertFalse(self.domain.flag)
        self.assertEqual(self.domain.counter, 2) # Incremented

    def test_flux_while(self):
        self.domain.counter = 0
        # Simulate: while domain.counter < 5: increment
        max_ops = 100
        ops = 0
        while self.domain.counter < 5 and ops < max_ops:
            p_increment(self.sys)
            ops += 1
        self.assertEqual(self.domain.counter, 5)

    def test_infinite_loop_safety(self):
        self.domain.counter = 0
        max_ops = 10
        ops = 0
        with self.assertRaises(RuntimeError):
            while True:
                p_increment(self.sys)
                ops += 1
                if ops >= max_ops:
                    raise RuntimeError(f"Infinite loop safety: exceeded {max_ops} ops")
        print(f"\nCaught Expected Safety Trip: loop exceeded {max_ops} ops")

if __name__ == '__main__':
    unittest.main()

