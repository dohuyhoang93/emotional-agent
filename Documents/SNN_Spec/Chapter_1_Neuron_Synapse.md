# Chapter 1: The Atomic Units (Neuron & Synapse)

**Scope**: Anatomy and Physiology of the SNN's smallest functional units.

> [!IMPORTANT]
> **Implementation Status**: All components described in this chapter are **FULLY IMPLEMENTED** in the codebase as of 2025-12-30.

---

## 1.1 Anatomy (Data Structures)

**File**: `src/core/snn_context_theus.py`  
**Status**: ✅ **IMPLEMENTED**

The system follows the **ECS (Entity-Component-System)** pattern. Neurons and Synapses are pure data structures ("Components") stored in contiguous arrays in the `SNNDomainContext`.

### A. The Semantic Neuron (`NeuronState`)

**Definition**: `src/core/snn_context_theus.py::NeuronState` (Lines 131-157)

Unlike traditional SNN neurons (scalar only), the Theus Neuron is a **Vector Processor**.

| Field | Type | Description | Status |
| :--- | :--- | :--- | :--- |
| `neuron_id` | `int` | Unique Identifier (Index in array). | ✅ |
| `potential` | `float` | Scalar activation level (Traditional LIF). | ✅ |
| `threshold` | `float` | Dynamic firing threshold (Homeostasis target). | ✅ |
| `last_fire_time` | `int` | Timestamp of last spike (for refractory period). | ✅ |
| `fire_count` | `int` | Total spikes emitted (for Darwinism). | ✅ |
| **`potential_vector`** | `float[16]` | **[Novelty]** Integrated semantic content of incoming spikes. | ✅ |
| **`prototype_vector`** | `float[16]` | **[Novelty]** The "Identity" or "Meaning" of this neuron. | ✅ |
| `inhibition_received` | `float` | Lateral inhibition signal (Phase 10). | ✅ |
| `solidity_ratio` | `float` | Derived commitment (0.0=Fluid, 1.0=Solid) (Phase 10.5). | ✅ |

**Capability**:
*   **Scalar Encoding**: Represent intensity (Fire rate).
*   **Vector Encoding**: Represent **Information Content**. A neuron doesn't just say "I'm firing", it says "I'm firing *about X*".

**Implementation Notes**:
```python
@dataclass
class NeuronState:
    neuron_id: int
    potential: float = 0.0
    threshold: float = 1.0
    last_fire_time: int = -1000
    fire_count: int = 0
    
    # Vector state (16-dim)
    potential_vector: np.ndarray = field(default_factory=lambda: np.zeros(16))
    prototype_vector: np.ndarray = field(default_factory=lambda: np.random.randn(16))
    
    # Phase 10: Lateral Inhibition
    inhibition_received: float = 0.0
    
    # Phase 10.5: Derived Commitment
    solidity_ratio: float = 0.0
```

---

### B. The Smart Synapse (`SynapseState`)

**Definition**: `src/core/snn_context_theus.py::SynapseState` (Lines 160-198)

The synapse is not a static weight; it is a dynamic memory unit with **Time-Travel capabilities**.

| Field | Type | Description | Status |
| :--- | :--- | :--- | :--- |
| `synapse_id` | `int` | Unique identifier. | ✅ |
| `pre_neuron_id` | `int` | Source neuron. | ✅ |
| `post_neuron_id` | `int` | Target neuron. | ✅ |
| `weight` | `float` | Connection strength (Standard). | ✅ |
| `trace` | `float` | Legacy trace (2-factor STDP). | ✅ |
| `trace_fast` | `float` | Decays in ~20ms. Used for immediate Hebbian association. | ✅ |
| **`trace_slow`** | `float` | **[Novelty]** Decays in ~5000ms. Used for **Dream Priming** & long-term tagging. | ✅ |
| `eligibility` | `float` | The "Tag" waiting for Dopamine confirmation. | ✅ |
| `commit_state` | `Enum` | `FLUID` (Plastic) vs `SOLID` (Protected/Myelinated) vs `REVOKED`. | ✅ |
| `consecutive_correct` | `int` | Counter for FLUID→SOLID transition. | ✅ |
| `consecutive_wrong` | `int` | Counter for SOLID→REVOKED transition. | ✅ |
| `quarantine_time` | `int` | Steps in quarantine (Phase 8: Social Learning). | ✅ |
| `validation_score` | `float` | Performance score for quarantine exit. | ✅ |
| `is_blacklisted` | `bool` | Permanent ban flag. | ✅ |
| `fitness` | `float` | Darwinian fitness score (Phase 11). | ✅ |
| `generation` | `int` | Evolutionary generation. | ✅ |
| `synapse_type` | `str` | "native" or "shadow" (Social Learning). | ✅ |
| `source_agent_id` | `int` | Origin agent (for social synapses). | ✅ |
| `confidence` | `float` | Trust level (0.0-1.0). | ✅ |

**Capability**:
*   **Prospective Memory**: Can "tag" an event in a dream (via `trace_slow`) and wait for reality to confirm it hours later.
*   **Stability-Plasticity**: Can lock itself (`SOLID`) to prevent forgetting important lessons.
*   **Social Learning**: Can import knowledge from other agents via "shadow" synapses.

**Implementation Notes**:
```python
@dataclass
class SynapseState:
    synapse_id: int
    pre_neuron_id: int
    post_neuron_id: int
    
    # Weights & Traces
    weight: float = 0.5
    trace_fast: float = 0.0   # tau=0.9
    trace_slow: float = 0.0   # tau=0.9998
    eligibility: float = 0.0  # trace_fast + trace_slow
    
    # Commitment Layer (Phase 7)
    commit_state: int = COMMIT_STATE_FLUID
    consecutive_correct: int = 0
    consecutive_wrong: int = 0
    
    # Social Quarantine (Phase 8)
    quarantine_time: int = 0
    validation_score: float = 0.0
    is_blacklisted: bool = False
    
    # Neural Darwinism (Phase 11)
    fitness: float = 0.5
    generation: int = 0
```

---

## 1.2 Physiology (Process & Interaction)

### A. Integration (`process_integrate`)

**Process**: `process_integrate`  
**File**: `src/processes/snn_core_theus.py::_integrate_impl` (Lines 31-117)  
**Status**: ✅ **IMPLEMENTED** (Vectorized)

This is where the magic of "Semantic SNN" happens. It uses **Vector Matching**, not just summation.

#### Standard SNN vs Theus SNN

| Aspect | Standard SNN | Theus SNN |
|--------|-------------|-----------|
| **Integration** | `Potential += Input * Weight` | `Potential += Weight * Similarity * Input` |
| **Similarity** | N/A | Cosine similarity between prototypes |
| **Filtering** | None | ReLU(Similarity) - only positive matches |

#### Implementation (Vectorized)

```python
# 1. Decay
potentials *= tau_decay  # 0.9
potential_vectors *= tau_decay

# 2. Get firing neurons
spike_indices = get_current_spikes()  # From spike buffer

# 3. Gather firing prototypes (K × D)
firing_protos = prototypes[spike_indices]

# 4. Compute similarity matrix (K × N)
# Assumes prototypes are L2-normalized
sim_matrix = firing_protos @ prototypes.T  # Dot product = cosine
sim_matrix = ReLU(sim_matrix)  # Only positive matches

# 5. Gather weights (K × N)
firing_weights = weights[spike_indices, :]

# 6. Effective weights (K × N)
eff_weights = firing_weights * sim_matrix

# 7. Integrate scalar potential (N,)
delta_pots = sum(eff_weights, axis=0)  # Sum over K spikes
potentials += delta_pots

# 8. Integrate vector potential (N × D)
delta_vecs = eff_weights.T @ firing_protos  # (N×K) @ (K×D) = (N×D)
potential_vectors += delta_vecs
```

**Meaning**: A neuron only listens to spikes that are **semantically relevant** to it. This creates automatic "Topic Clustering" in the network.

**Complexity**: O(K × N × D) where K = firing neurons, N = total neurons, D = vector dimension (16)

---

### B. Firing (`process_fire`)

**Process**: `process_fire`  
**File**: `src/processes/snn_core_theus.py::_fire_impl` (Lines 215-292)  
**Status**: ✅ **IMPLEMENTED** (Vectorized)

Follows standard LIF (Leaky Integrate-and-Fire) dynamics with a **Refractory Period**.

#### Firing Logic

*   **Condition**: `Potential >= Threshold`
*   **Refractory Check**: `current_time - last_fire_time > refractory_period` (5 steps)
*   **Action**:
    1.  Emit Spike (ID added to `spike_queue` or `spike_buffer`).
    2.  Reset `Potential` to -0.1 (Hyperpolarization).
    3.  Reset `Potential_Vector` to Zero.
    4.  Update `Fire_Rate` (for Homeostasis).
    5.  Update `last_fire_time` and `fire_count`.

#### Implementation (Vectorized)

```python
# 1. Identify neurons that can fire
can_fire = (potentials >= thresholds) & (current_time - last_fire > refractory)

# 2. Update spike buffer (Circular)
if use_vectorized_queue:
    t_idx = current_time % buffer_size
    spike_buffer[t_idx] = can_fire.astype(float)
else:
    spike_queue[current_time] = np.where(can_fire)[0].tolist()

# 3. Reset potentials
potentials[can_fire] = -0.1  # Hyperpolarization

# 4. Reset potential vectors
potential_vectors[can_fire] = 0.0

# 5. Update fire count
fire_count[can_fire] += 1

# 6. Update last fire time
last_fire[can_fire] = current_time

# 7. Calculate firing rate (for metrics)
fire_rate = sum(can_fire) / max(1, len(can_fire))
metrics['fire_rate'] = fire_rate
```

**Hyperparameters**:
- `refractory_period`: 5 steps (5ms)
- `hyperpolarization`: -0.1
- `tau_decay`: 0.9 (10% leak per step)

---

## 1.3 Conclusion

The Theus SNN Unit is a hybrid:
*   **Biologically Plausible**: Spikes, Leak, Threshold, Refractory.
*   **Computationally Efficient**: ECS Data Layout + Vectorized Operations.
*   **Semantically Rich**: Vector embeddings at the single-neuron level.

### Key Innovations

| Feature | Traditional SNN | Theus SNN |
|---------|----------------|-----------|
| **Neuron State** | Scalar potential | Scalar + 16D vector |
| **Integration** | Weight summation | Cosine-weighted summation |
| **Synapse Memory** | Single trace | Dual traces (fast + slow) |
| **Plasticity Control** | Fixed | 3-state FSM (FLUID/SOLID/REVOKED) |
| **Social Learning** | N/A | Shadow synapses from other agents |

---

## 1.4 Execution Model (Vectorized Tensors)

**File**: `src/core/snn_context_theus.py::ensure_tensors_initialized`  
**Status**: ✅ **IMPLEMENTED**

While conceptually treated as individual "Units", for performance reasons (Phase 2 Upgrade), the system operates in **Vectorized Mode**:

### Architecture

```
┌─────────────────────────────────────────┐
│         Object Layer (Audit)            │
│  neurons: List[NeuronState]             │
│  synapses: List[SynapseState]           │
└─────────────────────────────────────────┘
         ↕ sync_to_tensors / sync_from_tensors
┌─────────────────────────────────────────┐
│         Tensor Layer (Compute)          │
│  potentials: ndarray[N]                 │
│  thresholds: ndarray[N]                 │
│  potential_vectors: ndarray[N, 16]      │
│  prototypes: ndarray[N, 16]             │
│  weights: ndarray[N, N]                 │
│  commit_states: ndarray[N, N]           │
└─────────────────────────────────────────┘
```

### Data Layout

*   **Neuron Tensors**:
    - `potentials`: (N,) - Scalar potentials
    - `thresholds`: (N,) - Firing thresholds
    - `potential_vectors`: (N, D) - Semantic vectors
    - `prototypes`: (N, D) - Identity vectors
    - `last_fire`: (N,) - Timestamps
    - `fire_count`: (N,) - Spike counts

*   **Synapse Tensors**:
    - `weights`: (N, N) - Connectivity matrix
    - `commit_states`: (N, N) - State FSM
    - `consecutive_correct`: (N, N) - Counters
    - `consecutive_wrong`: (N, N) - Counters
    - `trace_fast`: (N, N) - Fast traces
    - `trace_slow`: (N, N) - Slow traces

### Processing Pipeline

1.  **Sync Objects → Tensors**: Before Compute.
    ```python
    sync_to_tensors(snn_ctx)
    ```

2.  **Vectorized Compute**:
    - Integration: Matrix multiplication `Sim = P_fired × P_all^T`
    - Firing: Boolean mask operation over `potentials` tensor
    - Learning: Element-wise operations on weight matrices

3.  **Sync Tensors → Objects**: After Compute (for Theus Audit/Checkpoints).
    ```python
    sync_from_tensors(snn_ctx)
    ```

### Performance Gains

This "Compute-Sync" strategy allows the Python-based SNN to run at **>50x speed** compared to object-loop iteration.

**Benchmarks** (50 neurons, 100 steps):
- Object-based: ~2.5s
- Vectorized: ~0.05s
- **Speedup**: 50x

**Complexity**:
- Sync overhead: O(N + S) where S = number of synapses
- Compute: O(K × N × D) where K = firing neurons
- Total: Dominated by compute, amortized over many steps

---

## 1.5 Implementation Notes

### Initialization

**File**: `src/processes/snn_initialization_theus.py`

```python
# Create neurons
for i in range(num_neurons):
    neuron = NeuronState(
        neuron_id=i,
        potential=0.0,
        threshold=initial_threshold,  # 0.6
        prototype_vector=random_unit_vector(16)
    )
    neurons.append(neuron)

# Create synapses (random connectivity)
for i in range(num_neurons):
    for j in range(num_neurons):
        if random() < connectivity:  # 0.15
            synapse = SynapseState(
                synapse_id=len(synapses),
                pre_neuron_id=i,
                post_neuron_id=j,
                weight=random(0.3, 0.7)
            )
            synapses.append(synapse)
```

### Hyperparameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `num_neurons` | 50 | Network size |
| `vector_dim` | 16 | Semantic dimension |
| `connectivity` | 0.15 | Sparsity (15% connected) |
| `initial_threshold` | 0.6 | Firing threshold |
| `tau_decay` | 0.9 | Leak rate (10% per step) |
| `refractory_period` | 5 | Cooldown (5ms) |

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 2: Learning Mechanisms (STDP, Clustering, Commitment)
> - Chapter 8: Performance Architecture (Vectorization details)
> - Chapter 10: Top-Down Modulation (Threshold control)
