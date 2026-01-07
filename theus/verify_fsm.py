
import sys
try:
    from theus_core import StateMachine
except ImportError:
    print("CRITICAL: theus_core not found.")
    sys.exit(1)

def test_fsm():
    print("\n--- Test Rust StateMachine ---")
    
    # 1. Define FSM Config
    fsm_def = {
        "IDLE": {
            "events": {
                "START": "RUNNING"
            },
            "process": "idle_process" # Legacy action key
        },
        "RUNNING": {
            "on": { # Legacy transition key
                "STOP": "IDLE",
                "PAUSE": "PAUSED"
            },
            "entry": ["log_start", "setup_resources"] # List of actions
        },
        "PAUSED": {
            "on": True, # Test Quirk: Boolean 'on' (should warn and ignore)
            "events": {
                "RESUME": "RUNNING"
            },
            "process": "pause_process"
        }
    }
    
    fsm = StateMachine(fsm_def, "IDLE")
    print(f"Initial State: {fsm.current_state}")
    assert fsm.current_state == "IDLE"
    
    # 2. Test Transition: IDLE -> START -> RUNNING
    print("Triggering 'START'...")
    actions = fsm.trigger("START")
    print(f" -> Current State: {fsm.current_state}")
    print(f" -> Actions: {actions}")
    
    assert fsm.current_state == "RUNNING"
    assert actions == ["log_start", "setup_resources"]
    
    # 3. Test Transition: RUNNING -> PAUSE -> PAUSED
    print("Triggering 'PAUSE'...")
    actions = fsm.trigger("PAUSE")
    print(f" -> Current State: {fsm.current_state}")
    print(f" -> Actions: {actions}")
    
    assert fsm.current_state == "PAUSED"
    assert actions == ["pause_process"]
    
    # 4. Test Transition: PAUSED -> RESUME -> RUNNING (Testing 'on': True quirk handling)
    # If 'on': True is treated as dict, it would crash or error. Rust should handle this.
    print("Triggering 'RESUME'...")
    actions = fsm.trigger("RESUME")
    print(f" -> Current State: {fsm.current_state}")
    
    assert fsm.current_state == "RUNNING"
    
    print("✅ StateMachine Logic Verified")

if __name__ == "__main__":
    test_fsm()
