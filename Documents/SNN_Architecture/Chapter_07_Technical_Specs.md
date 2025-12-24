# Chương 07: Đặc tả Kỹ thuật (Technical Specifications) - Consolidated

Đặc tả chi tiết cấu trúc dữ liệu và thuật toán, tích hợp Vector Spike, Multi-Trace, Commitment và Sandbox.

---

## 7.1 Database Schema (Unified ECS Model)

```python
from dataclasses import dataclass
import numpy as np

# Constants
VECTOR_DIM = 16
COMMIT_STATE_FLUID = 0
COMMIT_STATE_SOLID = 1
COMMIT_STATE_REVOKED = 2

# Sandbox Types
SYNAPSE_TYPE_NATIVE = 0
SYNAPSE_TYPE_SHADOW = 1 # Parasitic/Viral

@dataclass
class NeuronRecord:
    id: int
    layer_idx: int
    
    # Vector State
    potential_vector: np.ndarray # Shape (16,)
    prototype_vector: np.ndarray # Shape (16,) - Pattern to match
    similarity_threshold: float  # [0..1]
    
    # Homeostasis State (PID Controlled)
    base_threshold: float
    firing_rate_avg: float
    
    # Metadata
    last_spike_time: int

@dataclass
class SynapseRecord:
    id: int
    source_id: int
    target_id: int
    synapse_type: int       # NATIVE or SHADOW
    
    # Weights & Delays
    weight: float           # Trust/Causal strength
    delay_ms: int
    
    # Traces for Credit Assignment
    trace_fast: float       # Decay ~20ms
    trace_slow: float       # Decay ~5000ms (Tagging)
    last_active_time: int
    
    # Commitment State
    state: int              # FLUID/SOLID/REVOKED
    confidence: float       # [0..1]
    prediction_error_accum: float
```

---

## 7.2 Core Processes (Vectorized & Committed & Sandbox)

### Process 1: Tích hợp & So Khớp (Integrate & Fire)
*(Giữ nguyên logic Vector Integration)*

### Process 2: Học Tập & Sandbox Audit

```python
def process_learning_audit(db, spiked_neurons, dopamine):
    for synapse in relevant_synapses:
        # A. STDP & Trace Update ... (như cũ)
        
        # B. Sandbox Logic (Shadow vs Native)
        if synapse.synapse_type == SYNAPSE_TYPE_SHADOW:
            # Shadow Synapse cũng học, nhưng không ảnh hưởng output ngay
            accumulate_shadow_stats(synapse)
            
            # Check Coup Condition (Điều kiện Đảo chính)
            if synapse.confidence > SUPERIORITY_THRESH and synapse.error < native_synapse.error:
                 # Đảo chính thành công
                 promote_shadow_to_native(synapse)
                 revoke_native_synapse(native_synapse)
                 log("Viral Knowledge took over!")

        # C. Commitment Logic ... (như cũ)
```

### Process 3: Meta-Homeostasis Control Loop (PID)

```python
def process_meta_homeostasis(db, stats):
    # 1. Control Threshold
    error_rate = stats.global_firing_rate - TARGET_FIRING_RATE
    delta_theta = PID_controller_theta.update(error_rate)
    apply_global_threshold_bias(db, delta_theta)
    
    # 2. Control Inhibition
    if stats.epilepsy_score > SAFE_LIMIT:
        increase_global_inhibition(db)
```

---

## 7.3 Giao diện SNN-RL (The Interface)
*(Giữ nguyên Population Code & Top-down Modulation)*
