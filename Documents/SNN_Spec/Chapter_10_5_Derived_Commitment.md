# Chapter 10.5: Derived Neuron Commitment

> **Status:** Draft / Implementation
> **Target Phase:** Phase 10.5 (Advanced Commitment)
> **Reference Component:** `src/processes/snn_commitment_theus.py`

## 1. Problem: The Granularity Mismatch

-   **Synaptic Commitment (Phase 7)**: Operates at the connection level (`Synapse`). A synapse becomes `SOLID` when it consistently predicts correctly.
-   **Neuron Modulation (Phase 10)**: Operates at the unit level (`Neuron`). The RL agent boosts the sensitivity of entire neurons.

**The Logic Gap**: We want to apply modulation *only* to stable, mature concepts ("Solid Neurons") to avoid amplifying noise (Novelty Masking risk). However, the system relies on Synaptic Solidity. A neuron might have 10 incoming synapses, where 1 is Solid and 9 are Fluid. Is the neuron "Solid"?

## 2. Concept: Derived Solidity Ratio

We introduce a **Derived State** for neurons, calculated from the bottom-up aggregation of their dendritic tree (incoming synapses).

### Definition
The `solidity_ratio` ($\rho$) of a neuron $j$ is the fraction of its valid incoming synapses that are in the `SOLID` state.

$$ \rho_j = \frac{\sum_{i \in Inputs} \mathbb{1}(Synapse_{i \to j} == SOLID)}{Total\_Incoming\_Synapses_j} $$

### Classification
-   **Fluid Identity ($\rho < 0.5$)**: The neuron is still forming its concept. It is dominated by plastic connections. *Modulation should be weak or disabled.*
-   **Solid Identity ($\rho \ge 0.5$)**: The neuron represents a stable, validated concept. *Modulation is fully enabled.*

## 3. Implementation Logic

### 3.1 Data Structure
-   **NeuronState**: Add `solidity_ratio: float` (Range 0.0 - 1.0).
-   **Tensors**: Add `solidity_ratios` (Shape `[N]`).

### 3.2 Calculation Process (`process_commitment`)
1.  **Update Synapses**: Existing Phase 7 logic updates `commit_state` (Fluid/Solid/Revoked).
2.  **Aggregate**:
    -   For each neuron, count `Incoming_Solid`.
    -   Count `Incoming_Total`.
    -   Compute $\rho$.
3.  **Vectorization Strategy**:
    -   Use `commit_states` matrix (`[N, N]`).
    -   Mask `solid_mask = (commit_states == 1)`.
    -   `solid_counts = solid_mask.sum(axis=0)` (Sum columns $\to$ incoming).
    -   `total_counts` can be derived from `weights > 0` or a separate adjacency mask.

### 3.3 Filtering Application (`modulate_snn_attention`)
-   **Input**: `solidity_ratios` tensor.
-   **Mask**: `ModulationMask = (ActionTarget) & (solidity_ratios > 0.5)`.
-   **Action**: Apply threshold reduction only to `ModulationMask`.

## 4. Benefit
This mechanism bridges the gap between low-level plasticity (Synapses) and high-level control (Neurons), allowing the RL agent to confidently manipulate "Concepts" without accidentally distorting the learning process of new memories.
