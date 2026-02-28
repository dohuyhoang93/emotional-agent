"""
SNN Recorder Process
====================
Process ghi lại SNN state vào buffer và flush ra file safely.

Tuân thủ POP và Safe I/O.
"""
import numpy as np
import gzip
import struct
import os
from theus.contracts import process
from src.core.context import SystemContext

# ============================================================================
# SNN Recorder Process
# ============================================================================

@process(
    inputs=['domain_ctx', 'domain_ctx.heavy_recorder_buffer', 'domain_ctx.snn_context'],
    outputs=['domain_ctx', 'domain_ctx.heavy_recorder_buffer'],
    side_effects=['io/disk']
)
def process_record_snn_step(ctx: SystemContext):
    """
    Ghi lại state SNN hiện tại vào buffer và flush nếu đầy.
    
    Yêu cầu: 
    - domain_ctx.heavy_recorder_buffer: List ([HEAVY ZONE])
    - domain_ctx.recorder_config: Dict {'output_dir': str, 'agent_id': int, 'buffer_size': int}
    """
    domain = ctx.domain_ctx
    snn_ctx = domain.snn_context
    buffer = domain.heavy_recorder_buffer
    
    # Check config
    config = getattr(domain, 'recorder_config', None)
    if config is None:
        return {} # Recorder not configured/enabled
        
    neurons = snn_ctx.domain_ctx.neurons
    
    # 1. Capture State
    # Only save potentials (float16) to save space
    potentials = np.array([n.potential for n in neurons], dtype=np.float16)
    
    # Firing indices (int16)
    firing_indices = [i for i, n in enumerate(neurons) if n.potential >= n.threshold]
    
    # Step/Ep info
    # Assuming current_episode/step are in domain
    ep = getattr(domain, 'current_episode', 0)
    st = getattr(domain, 'current_step', 0)
    
    frame = {
        'ep': ep,
        'st': st,
        'p': potentials,
        'f': np.array(firing_indices, dtype=np.int16)
    }
    
    # 2. Append (Linear accumulation)
    buffer.append(frame)
    
    # 3. Check Buffer Size
    buffer_size = config.get('buffer_size', 1000)
    if len(buffer) >= buffer_size:
        _flush_buffer_safely(buffer, config)
    return {}


def _flush_buffer_safely(buffer: list, config: dict):
    """
    Flush buffer với cơ chế try-finally để đảm bảo Memory Safety.
    """
    output_dir = config.get('output_dir', 'results/recordings')
    agent_id = config.get('agent_id', 0)
    filename = f"recording_agent_{agent_id}.bin.gz"
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Ensure dir exists (Check once ideally, but IO overhead is negligible compared to 1000 steps)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        with gzip.open(filepath, 'ab') as f:
            for frame in buffer:
                 # Frame Format:
                # [Ep:H] [Step:H] [NumNeurons:H] [Potentials:Num*2 bytes] [NumSpikes:H] [SpikeIndices:NumSpikes*2 bytes]
                
                ep = struct.pack('H', frame['ep']) # Unsigned short (max 65535 eps)
                st = struct.pack('H', frame['st']) # Unsigned short (max 65535 steps)
                
                pots = frame['p'].tobytes()
                num_neurons = struct.pack('H', len(frame['p']))
                
                spikes = frame['f'].tobytes()
                num_spikes = struct.pack('H', len(frame['f']))
                
                f.write(ep + st + num_neurons + pots + num_spikes + spikes)
                
    except Exception as e:
        # Log error to stderr manually since Theus might swallow it
        import sys
        print(f"[RecorderError] Agent {agent_id} Failed to flush: {e}", file=sys.stderr)
        # We DO NOT re-raise to crash loop. We drop frame data to save memory.
        
    finally:
        # SECURITY/MEMORY CRITICAL: Always clear buffer!
        buffer.clear()
