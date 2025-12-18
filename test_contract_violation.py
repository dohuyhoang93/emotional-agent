import unittest
from src.core.engine import POPEngine, process, ContractViolationError
from src.core.context import SystemContext, GlobalContext, DomainContext
import torch

class TestContractEnforcement(unittest.TestCase):
    def setUp(self):
        # Setup Dummy Context
        global_ctx = GlobalContext(
            initial_needs=[0.5], initial_emotions=[0.0], total_episodes=1, max_steps=10, seed=42
        )
        domain_ctx = DomainContext(
            N_vector=torch.tensor([0.5]), E_vector=torch.tensor([0.0]),
            believed_switch_states={}, q_table={}, short_term_memory=[], long_term_memory={}
        )
        self.sys_ctx = SystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)
        self.engine = POPEngine(self.sys_ctx)

    def test_illegal_write_violation(self):
        """Test catching a write to an undeclared output."""
        
        # Define a process that writes to 'domain.td_error' but does NOT declare it
        @process(inputs=[], outputs=['domain.current_step']) # Missing 'domain.td_error'
        def bad_writer(ctx):
            ctx.domain_ctx.current_step = 1 # OK
            ctx.domain_ctx.td_error = 0.5   # VIOLATION!
            
        self.engine.register_process("bad_writer", bad_writer)
        
        print("\n[Test] Illegal Write Violation...")
        with self.assertRaises(ContractViolationError) as cm:
            self.engine.run_process("bad_writer")
        
        print(f"   -> Caught Expected Error: {cm.exception}")
        self.assertIn("Illegal Write Violation", str(cm.exception))
        self.assertIn("domain.td_error", str(cm.exception))

    def test_undeclared_error_violation(self):
        """Test catching an undeclared exception."""
        
        @process(inputs=[], outputs=[], errors=['ValueError']) # Declares ValueError
        def bad_error(ctx):
            raise TypeError("I am a TypeError") # VIOLATION (Not in errors list)
            
        self.engine.register_process("bad_error", bad_error)
        
        print("\n[Test] Undeclared Error Violation...")
        with self.assertRaises(ContractViolationError) as cm:
            self.engine.run_process("bad_error")
            
        print(f"   -> Caught Expected Error: {cm.exception}")
        self.assertIn("Undeclared Error Violation", str(cm.exception))
        self.assertIn("TypeError", str(cm.exception))

    def test_valid_execution(self):
        """Test that valid contracts pass."""
        
        @process(inputs=[], outputs=['domain.current_step'])
        def good_process(ctx):
            ctx.domain_ctx.current_step = 99
            
        self.engine.register_process("good_process", good_process)
        
        self.engine.run_process("good_process")
        self.assertEqual(self.sys_ctx.domain_ctx.current_step, 99)
        print("\n[Test] Valid Execution -> OK")

if __name__ == "__main__":
    unittest.main()
