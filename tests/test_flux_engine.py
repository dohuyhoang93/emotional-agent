
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
        self.engine = TheusEngine(self.sys, strict_mode=False)
        self.engine.register_process("increment", p_increment)
        self.engine.register_process("set_flag", p_set_flag_true)
        self.engine.register_process("reset", p_reset_counter)

    def test_flux_run_simple(self):
        steps = [
            {'flux': 'run', 'steps': ['increment', 'increment']}
        ]
        # Manually invoke _execute_step or execute_workflow stub
        # Since execute_workflow reads file, let's call _execute_step directly loop
        self.engine._flux_ops_count = 0
        self.engine._flux_max_ops = 100
        for step in steps:
            self.engine._execute_step(step)
            
        self.assertEqual(self.domain.counter, 2)

    def test_flux_if(self):
        self.domain.counter = 5
        step = {
            'flux': 'if',
            'condition': 'domain.counter > 3',
            'then': ['set_flag'],
            'else': ['increment']
        }
        self.engine._flux_ops_count = 0
        self.engine._flux_max_ops = 100
        self.engine._execute_step(step)
        self.assertTrue(self.domain.flag)
        self.assertEqual(self.domain.counter, 5) # Not incremented

    def test_flux_if_else(self):
        self.domain.counter = 1
        step = {
            'flux': 'if',
            'condition': 'domain.counter > 3',
            'then': ['set_flag'],
            'else': ['increment']
        }
        self.engine._flux_ops_count = 0
        self.engine._flux_max_ops = 100
        self.engine._execute_step(step)
        self.assertFalse(self.domain.flag)
        self.assertEqual(self.domain.counter, 2) # Incremented

    def test_flux_while(self):
        self.domain.counter = 0
        step = {
            'flux': 'while',
            'condition': 'domain.counter < 5',
            'do': ['increment']
        }
        self.engine._flux_ops_count = 0
        self.engine._flux_max_ops = 100
        self.engine._execute_step(step)
        self.assertEqual(self.domain.counter, 5)

    def test_infinite_loop_safety(self):
        self.domain.counter = 0
        self.engine._flux_max_ops = 10 # Low limit
        step = {
            'flux': 'while',
            'condition': 'True', # Infinite
            'do': ['increment']
        }
        
        with self.assertRaises(RuntimeError) as cm:
            self.engine._execute_step(step)
        
        print(f"\nCaught Expected Safety Trip: {cm.exception}")

if __name__ == '__main__':
    unittest.main()
