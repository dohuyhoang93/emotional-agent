import asyncio
import pytest
from theus import TheusEngine
from theus.contracts import OutboxMsg

async def verify_rollback():
    print("=== Verifying Native Outbox Rollback ===")
    engine = TheusEngine()
    
    # 1. Happy Path
    print("[Step 1] Testing Commit...")
    with engine.transaction() as tx:
        tx.outbox.add(OutboxMsg("test_topic", "commit_payload"))
    
    # Verify it made it to engine
    # We can't access engine.outbox directly from Python easily if not exposed?
    # engine.process_outbox() calls the worker.
    
    received = []
    def worker(msg):
        received.append(msg)
    
    engine.attach_worker(worker)
    engine.process_outbox()
    
    if len(received) == 1 and received[0].payload == "commit_payload":
        print("   ✅ Commit worked (Baseline)")
    else:
        print(f"   ❌ Baseline Failed: {len(received)}")
        return

    # 2. Rollback Path
    print("\n[Step 2] Testing Rollback (Exception)...")
    try:
        with engine.transaction() as tx:
            tx.outbox.add(OutboxMsg("test_topic", "rollback_payload"))
            raise ValueError("Intentional Failure")
    except ValueError:
        print("   Caught intentional error.")

    # Verify outbox is empty
    received.clear()
    engine.process_outbox() # Should operate on empty queue
    
    if len(received) == 0:
        print("   ✅ Rollback Successful: Message discarded.")
    else:
        print(f"   ❌ Rollback FAILED: Message persisted! {received[0].payload}")

if __name__ == "__main__":
    asyncio.run(verify_rollback())
