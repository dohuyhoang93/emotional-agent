"""
Minimal debug script to trace ctx.outbox access path.
"""
import asyncio
from theus import TheusEngine
from theus import process
from theus_core import OutboxMsg

engine = TheusEngine()
engine.compare_and_swap(0, {"domain": {"status": "init"}})

received = []
engine.attach_worker(lambda m: received.append(m))

@process(outputs=["domain.status"])
async def test_outbox(ctx):
    print(f"[DEBUG] ctx type: {type(ctx)}", flush=True)
    print(f"[DEBUG] ctx.__class__.__name__: {ctx.__class__.__name__}", flush=True)
    
    # Try to access outbox
    try:
        outbox = ctx.outbox
        print(f"[DEBUG] ctx.outbox type: {type(outbox)}", flush=True)
        print(f"[DEBUG] ctx.outbox repr: {repr(outbox)}", flush=True)
        
        # Try to add a message
        outbox.add(OutboxMsg("test_topic", "test_payload"))
        print(f"[DEBUG] outbox.add succeeded", flush=True)
    except Exception as e:
        print(f"[DEBUG] ctx.outbox access error: {e}", flush=True)
    
    return "done"

engine.register(test_outbox)

async def main():
    await engine.execute("test_outbox")
    print(f"[DEBUG] After execute, calling flush_outbox on engine...", flush=True)
    if hasattr(engine._core, 'flush_outbox'):
        engine._core.flush_outbox()
        print(f"[DEBUG] engine._core.flush_outbox() called", flush=True)
    print(f"[DEBUG] Calling engine.process_outbox()...", flush=True)
    engine.process_outbox()
    print(f"[RESULT] received messages: {len(received)}", flush=True)
    for msg in received:
        print(f"  - {msg.topic}: {msg.payload}", flush=True)

asyncio.run(main())
