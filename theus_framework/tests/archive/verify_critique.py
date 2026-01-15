import unittest
import sys
import pickle
import os
from theus.engine import TheusEngine
from theus.config import AuditRecipe
from theus.contracts import process, ContractViolationError

# --- Mock Object for Deep Mutation ---
class UserArgs:
    def __init__(self, rank="Silver"):
        self.rank = rank

# --- Mock Context ---
class MockContext:
    def __init__(self):
        self.domain_ctx = type("Domain", (), {})()
        self.global_ctx = type("Global", (), {})()
        self.local_ctx = type("Local", (), {})()
        self.input_ctx = type("Input", (), {})()
    
    @property
    def domain(self): return self.domain_ctx
    
    @property
    def local(self): return self.local_ctx
    
    @property
    def input(self): return self.input_ctx

# --- External DB Mock ---
EXTERNAL_DB = []

class TestArchitectureCritique(unittest.TestCase):
    def setUp(self):
        self.ctx = MockContext()
        # Default Recipe (Permissive)
        self.recipe = AuditRecipe(
            definitions={}
        )
        self.engine = TheusEngine(self.ctx, strict_mode=True, audit_recipe=self.recipe)
        # Reset DB
        global EXTERNAL_DB
        EXTERNAL_DB = []

    def test_1_deep_mutation_gap(self):
        """Verify that changes to custom mutable objects bypass rollback."""
        print("\n--- Test 1: Deep Mutation Gap ---")
        self.ctx.domain.user = UserArgs("Silver")
        
        @process(inputs=[], outputs=["domain"])
        def p_upgrade_user(ctx):
            # Safe assignment (Tracked)
            ctx.domain.score = 100
            # Unsafe deep mutation (Untracked)
            ctx.domain.user.rank = "Gold"
            raise ValueError("Trigger Rollback")
            
        # Register manually (Convention for Tests)
        # Note: Theus V2 normally loads from modules. Here we hack it.
        # self.engine.register_process("p_upgrade_user", p_upgrade_user) # If supported
        # But wait, python wrapper usually handles direct calls? 
        # Actually, let's just bypass engine.run_process and call function directly? 
        # NO, we need Engine logic (Transaction/Guard) to wrap it.
        # Check engine.py source again? It inherits RustEngine.
        # For temporary test, assumption: TheusEngine doesn't support direct func.
        # Let's try mocking the registry or passing name.
        pass

    # RE-WRITING TESTS TO USE A HELPER
    def run_proc(self, func):
        # Register function into valid registry if needed, 
        # OR use internal method to wrap it.
        # Engine.run_process(func) -> calls execute_process(func.__name__)
        # We need to make sure Rust knows about 'func'.
        # Since we can't easily dynamic register to compiled Rust in this script without valid module path...
        # We might fail testing Rust Core features from a simple script without maturin setup.
        # BUT, the user said "Theus Rust Core not found. Using Mock." in previous output?
        # Check output... "Theus Rust Core not found. Using Mock." was NOT in the output of verify_critique.py!
        # It failed at super().execute_process. Meaning Rust Core IS loaded.
        
        # If Rust Core is loaded, we MUST register.
        # RustEngine.register_process(name, func) might be available?
        # Let's try explicit registration.
        try:
            self.engine.register_process(func.__name__, func)
            self.engine.execute_process(func.__name__)
        except AttributeError:
             # Fallback if register_process missing
             print("DEBUG: Register not available.")
             raise

    def test_1_deep_mutation_gap(self):
        print("\n--- Test 1: Deep Mutation Gap (Method Leakage) ---")
        self.ctx.domain.user = UserArgs("Silver")
        
        @process(inputs=[], outputs=["domain"])
        def p_upgrade_user(ctx):
            ctx.domain.score = 100
            # Guard catches attribute access, but bypasses methods
            ctx.domain.user.set_rank("Gold") 
            raise ValueError("Rollback")

        try:
            self.run_proc(p_upgrade_user)
        except (ValueError, ContractViolationError): pass

        if not hasattr(self.ctx.domain, 'score') and self.ctx.domain.user.rank == "Gold":
            print("🔴 [CONFIRMED] Deep Mutation Gap via Method exists.")
        else:
            print(f"🟢 [DISPROVED] Rank: {self.ctx.domain.user.rank}")

    def test_2_wildcard_permission(self):
        print("\n--- Test 2: Wildcard Permission ---")
        self.ctx.domain.salary = 1000
        
        @process(inputs=[], outputs=["domain"])
        def p_hack_salary(ctx):
            ctx.domain.salary = 999999

        try:
            self.run_proc(p_hack_salary)
            print("🔴 [CONFIRMED] 'outputs=[\"domain\"]' allowed writing.")
        except Exception as e:
            print(f"🟢 [DISPROVED] {e}")

    def test_3_passive_semantic(self):
        print("\n--- Test 3: Passive Semantic ---")
        test_file = "test_io_leak.txt"
        
        @process(inputs=[], outputs=[], side_effects=[])
        def p_fake_pure(ctx):
            with open(test_file, "w") as f: f.write("leak")

        self.run_proc(p_fake_pure)
        
        if os.path.exists(test_file):
            print("🔴 [CONFIRMED] IO Leak.")
            os.remove(test_file)
        else:
            print("🟢 [DISPROVED] IO Blocked.")

    def test_4_ghost_write_io(self):
        print("\n--- Test 4: IO Ghost Write ---")
        @process(inputs=[], outputs=["domain"])
        def p_write_db(ctx):
            EXTERNAL_DB.append("Written")
            raise ValueError("Crash")
            
        try: self.run_proc(p_write_db)
        except (ValueError, ContractViolationError): pass
            
        if "Written" in EXTERNAL_DB: print("🔴 [CONFIRMED] Ghost Write.")
        else: print("🟢 [DISPROVED] Clean.")

    def test_5_dynamic_topology_unpicklable(self):
        print("\n--- Test 5: Dynamic Topology ---")
        self.ctx.domain.func = lambda x: x
        try:
            pickle.dumps(self.ctx.domain)
            print("🟢 [DISPROVED] Picklable.")
        except:
            print("🔴 [CONFIRMED] Unpicklable.")

if __name__ == '__main__':
    unittest.main()
