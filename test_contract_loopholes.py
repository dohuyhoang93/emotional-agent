import unittest
from src.core.engine import POPEngine, process
from src.core.context import SystemContext, GlobalContext, DomainContext
import torch

class TestContractLoopholes(unittest.TestCase):
    def setUp(self):
        # Setup Dummy Context
        global_ctx = GlobalContext(
            initial_needs=[0.5], initial_emotions=[0.0], total_episodes=1, max_steps=10, seed=42
        )
        domain_ctx = DomainContext(
            N_vector=torch.tensor([0.5]), E_vector=torch.tensor([0.0]),
            believed_switch_states={}, 
            q_table={}, 
            short_term_memory=[1, 2, 3], # Mutable List
            long_term_memory={}
        )
        self.sys_ctx = SystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)
        self.engine = POPEngine(self.sys_ctx)

    def test_loophole_read_violation(self):
        """Loophole 1: Reading a variable NOT in inputs."""
        print("\n[Loophole 1] Testing Undeclared Read...")
        
        @process(inputs=[], outputs=[]) 
        def sneaky_reader(ctx):
            # We did NOT declare 'domain.N_vector' in inputs
            secret = ctx.domain_ctx.N_vector 
            print(f"   -> Stole secret value: {secret}")
            
        self.engine.register_process("sneaky_reader", sneaky_reader)
        
        try:
            self.engine.run_process("sneaky_reader")
            print("   -> FAIL: Engine allowed undeclared read.")
        except Exception as e:
            print(f"   -> PASS: Caught read violation: {e}")

    def test_loophole_mutable_mutation(self):
        """Loophole 2: Modifying a mutable object in-place (bypassing setattr)."""
        print("\n[Loophole 2] Testing Mutable Object Mutation...")
        
        @process(inputs=['domain.short_term_memory'], outputs=[]) 
        def trojan_writer(ctx):
            # We declared it as INPUT (Read-Only intent usually), but not OUTPUT.
            # However, because it's a list, we can append to it.
            # ContextGuard only blocks 'ctx.domain.x = y', not 'ctx.domain.x.append(y)'
            ctx.domain_ctx.short_term_memory.append(9999)
            print("   -> Injected 9999 into short_term_memory.")
            
        self.engine.register_process("trojan_writer", trojan_writer)
        
        from theus import ContractViolationError
        try:
            self.engine.run_process("trojan_writer")
            # If we reach here, either it worked (bad) or swallowed (maybe bad)
            print("   -> FAIL: Engine allowed execution without error.")
        except ContractViolationError:
             print("   -> PASS: Engine prevented mutation (Immutable Violation).")
             return

        if 9999 in self.sys_ctx.domain_ctx.short_term_memory:
            self.fail("Engine allowed in-place mutation of undeclared output.")

    def test_loophole_side_effect(self):
        """Loophole 3: Direct Import Side Effect."""
        print("\n[Loophole 3] Testing Direct Side Effects...")
        
        @process(inputs=[], outputs=[], side_effects=[]) # No side effects declared
        def hacker(ctx):
            import os
            print("   -> I am printing to console directly (Side Effect!)")
            # os.system("echo 'I could delete your files'") 
            
        self.engine.register_process("hacker", hacker)
        self.engine.run_process("hacker")
        print("   -> FAIL: Engine allowed direct I/O.")

if __name__ == "__main__":
    unittest.main()
