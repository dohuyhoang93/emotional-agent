import struct
import numpy as np
import os
import gzip

class SNNRecorder:
    """
    Hộp đen ghi lại hoạt động SNN (Blackbox Recorder).
    
    Logic:
    - Buffers data in memory.
    - Flushes to compressed binary file periodically.
    - Minimal impact on simulation speed.
    """
    def __init__(self, agent_id, output_dir, buffer_size=1000):
        self.agent_id = agent_id
        self.output_dir = output_dir
        self.buffer_size = buffer_size
        self.buffer = []
        
        # Ensure dir
        os.makedirs(output_dir, exist_ok=True)
        self.filepath = os.path.join(output_dir, f"recording_agent_{agent_id}.bin.gz")
        
        # Reset file
        with gzip.open(self.filepath, 'wb') as f:
            # Write Header if needed (e.g. version)
            pass
            
    def record_step(self, snn_ctx, episode, step):
        """
        Ghi lại trạng thái tại 1 bước.
        Saves: [Episode, Step, NeuronPotentials, SpikeCount]
        """
        neurons = snn_ctx.domain_ctx.neurons
        
        # Optimize: Only save potentials (float16) to save space
        potentials = np.array([n.potential for n in neurons], dtype=np.float16)
        
        # Firing neurons (bitmask or list of indices)
        # For visualization, potentials usually enough as spikes are visible as peaks > threshold
        # OR we save index of firing neurons
        firing_indices = [i for i, n in enumerate(neurons) if n.potential >= n.threshold]
        
        frame = {
            'ep': episode,
            'st': step,
            'p': potentials,
            'f': np.array(firing_indices, dtype=np.int16) # Indices
        }
        
        self.buffer.append(frame)
        
        if len(self.buffer) >= self.buffer_size:
            self.flush()
            
    def flush(self):
        """Flush buffer to disk."""
        if not self.buffer: return
        
        with gzip.open(self.filepath, 'ab') as f:
            for frame in self.buffer:
                # Frame Format:
                # [Ep:H] [Step:H] [NumNeurons:H] [Potentials:Num*2 bytes] [NumSpikes:H] [SpikeIndices:NumSpikes*2 bytes]
                
                ep = struct.pack('H', frame['ep']) # Unsigned short (max 65535 eps)
                st = struct.pack('H', frame['st']) # Unsigned short (max 65535 steps)
                
                pots = frame['p'].tobytes()
                num_neurons = struct.pack('H', len(frame['p']))
                
                spikes = frame['f'].tobytes()
                num_spikes = struct.pack('H', len(frame['f']))
                
                f.write(ep + st + num_neurons + pots + num_spikes + spikes)
                
        self.buffer.clear()
        
    def close(self):
        self.flush()
