import os
import json
import glob
import numpy as np

# Adjust module path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.snn_context_theus import SNNGlobalContext, SNNDomainContext, SNNSystemContext, NeuronState, SynapseState
from src.tools.brain_biopsy_theus import BrainBiopsyTheus

# Find latest checkpoint
chkpts = glob.glob('results/multi_agent_complex_maze/checkpoint_ep_*')
if not chkpts:
    print('No checkpoints found. Vui lòng đảm bảo thử nghiệm Complex Maze đã lưu checkpoint.')
    exit()

def get_ep(p):
    try: return int(os.path.basename(p).split('_')[-1])
    except: return -1

latest_chkpt = max(chkpts, key=get_ep)
snn_file = os.path.join(latest_chkpt, 'agent_0_snn.json')
if not os.path.exists(snn_file):
    print(f'SNN file not found: {snn_file}')
    exit()

print(f"Loading checkpoint: {latest_chkpt}")

# Fake initialization according to experiments.json (num_neurons=1024, vector_dim=16)
global_ctx = SNNGlobalContext(num_neurons=1024, vector_dim=16, connectivity=0.1, seed=42)
domain_ctx = SNNDomainContext(global_ctx)

# Create mock neurons
for i in range(1024):
    neuron = NeuronState(
        neuron_id=i,
        prototype_vector=np.zeros(16, dtype=np.float32),
        threshold=0.05
    )
    domain_ctx.neurons.append(neuron)

# Create context
snn_ctx = SNNSystemContext(global_ctx=global_ctx, domain_ctx=domain_ctx)

try:
    with open(snn_file, 'r') as f:
        data = json.load(f)
    if 'synapses' in data:
        for s in data['synapses']:
            # Dựng lại bộ khung synapses từ checkpoint để bypass lỗi thiếu khớp nối
            synapse = SynapseState(
                synapse_id=s['synapse_id'],
                pre_neuron_id=s['pre_neuron_id'],
                post_neuron_id=s.get('post_neuron_id', 0),
                weight=s.get('weight', 0.5)
            )
            domain_ctx.synapses.append(synapse)
            
    # Tiến hành Hydration (Đổ dữ liệu)
    BrainBiopsyTheus.load_agent_checkpoint(snn_file, snn_ctx)
    print("Checkpoint loaded successfully.\n")
    
    print("="*50)
    print("🧠 SNN BIOPSY REPORT - POPULATION")
    print("="*50)
    print(json.dumps(BrainBiopsyTheus.inspect_population(snn_ctx), indent=2))
    
    print("\n" + "="*50)
    print("🔗 SNN BIOPSY REPORT - CAUSALITY LEARNING")
    print("="*50)
    print(json.dumps(BrainBiopsyTheus.inspect_causality(snn_ctx, threshold=0.7), indent=2))
    
except Exception as e:
    import traceback
    traceback.print_exc()
