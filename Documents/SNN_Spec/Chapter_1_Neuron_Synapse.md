# Chapter 1: The Atomic Units (Neuron & Synapse)

**Scope**: Anatomy and Physiology of the SNN's smallest functional units.

## 1.1 Anatomy (Data Structures)
The system follows the **ECS (Entity-Component-System)** pattern. Neurons and Synapses are pure data structures ("Components") stored in contiguous arrays in the `SNNDomainContext`.

### A. The Semantic Neuron (`NeuronState`)
Unlike traditional SNN neurons (scalar only), the Theus Neuron is a **Vector Processor**.

| Field | Type | Description |
| :--- | :--- | :--- |
| `neuron_id` | `int` | Unique Identifier (Index in array). |
| `potential` | `float` | Scalar activation level (Traditional LIF). |
| `threshold` | `float` | Dynamic firing threshold (Homeostasis target). |
| **`potential_vector`** | `float[16]` | **[Novelty]** Integrated semantic content of incoming spikes. |
| **`prototype_vector`** | `float[16]` | **[Novelty]** The "Identity" or "Meaning" of this neuron. |

**Capability**:
*   **Scalar Encoding**: Represent intensity (Fire rate).
*   **Vector Encoding**: Represent **Information Content**. A neuron doesn't just say "I'm firing", it says "I'm firing *about X*".

### B. The Smart Synapse (`SynapseState`)
The synapse is not a static weight; it is a dynamic memory unit with **Time-Travel capabilities**.

| Field | Type | Description |
| :--- | :--- | :--- |
| `weight` | `float` | Connection strength (Standard). |
| `trace_fast` | `float` | Decays in ~20ms. Used for immediate Hebbian association. |
| **`trace_slow`** | `float` | **[Novelty]** Decays in ~5000ms. Used for **Dream Priming** & long-term tagging. |
| `eligibility` | `float` | The "Tag" waiting for Dopamine confirmation. |
| `commit_state` | `Enum` | `FLUID` (Plastic) vs `SOLID` (Protected/Myelinated). |

**Capability**:
*   **Prospective Memory**: Can "tag" an event in a dream (via `trace_slow`) and wait for reality to confirm it hours later.
*   **Stability-Plasticity**: Can lock itself (`SOLID`) to prevent forgetting important lessons.

## 1.2 Physiology (Process & Interaction)

### A. Integration (`process_integrate`)
This is where the magic of "Semantic SNN" happens. It uses **Vector Matching**, not just summation.

*   **Standard SNN**: `Potential += Input * Weight`
*   **Theus SNN**: Uses **Cosine Similarity** to filter noise.
    ```python
    # Cosine Similarity = (A . B) / (|A| * |B|)
    Similarity = Dot(Spike_Vector, Post_Vector) / (Norm(Spike) * Norm(Post))
    
    # Weight Modulation: Only pass signal if vectors align (Relu)
    Effective_Weight = Weight * max(0, Similarity)
    Potential += Effective_Weight
    ```
*   **Meaning**: A neuron only listens to spikes that are **semantically relevant** to it. This creates automatic "Topic Clustering" in the network.

### B. Firing (`process_fire`)
Follows standard LIF (Leaky Integrate-and-Fire) dynamics with a **Refractory Period**.

*   **Condition**: `Potential >= Threshold`
*   **Action**:
    1.  Emit Spike (ID added to `spike_queue`).
    2.  Reset `Potential` to -0.1 (Hyperpolarization).
    3.  Reset `Potential_Vector` to Zero.
    4.  Update `Fire_Rate` (for Homeostasis).

## 1.3 Conclusion
The Theus SNN Unit is a hybrid:
*   **Biologically Plausible**: Spikes, Leak, Threshold, Refractory.
*   **Computationally Efficient**: ECS Data Layout.
*   **Semantically Rich**: Vector embeddings at the single-neuron level.

## 1.4 Execution Model (Vectorized Tensors)
While conceptually treated as individual "Units", for performance reasons (Phase 2 Upgrade), the system operates in **Vectorized Mode**:
*   **Data Layout**: All neuron states (`potentials`, `thresholds`, `vectors`) are synced to **NumPy Tensors** (Matrices) at the start of a cycle.
*   **Processing**:
    *   Integration is a single Matrix Multiplication: $Sim = P_{fired} \times P_{all}^T$.
    *   Firing is a boolean mask operation over the `Potentials` tensor.
*   **Sync Strategy**:
    *   `Objects -> Tensors`: Before Compute.
    *   `Tensors -> Objects`: After Compute (to maintain compatibility with Theus Audit/Checkpoints).
This "Compute-Sync" strategy allows the Python-based SNN to run at **>50x speed** compared to object-loop iteration.
