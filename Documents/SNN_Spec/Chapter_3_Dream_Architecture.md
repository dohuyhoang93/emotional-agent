# Chapter 3: Semantic Dream & Protection Architecture

**Scope**: How the agent simulates reality, learns from it, and protects itself from "mental crashes".

## 3.1 The Dream Cycle (Simulation)
Dreams in Theus SNN are not random noise; they are **Constructed Simulations**.

### A. Genesis (`process_imagination_loop`)
*   **Mechanism**: The agent disconnects from sensory input (Sleep Paralysis).
*   **Input**: It picks a random "Seed Neuron" and injects its `prototype_vector` back into the network.
*   **Propagation**: The network naturally associates from this seed (associative memory replay).

### B. Decoding (`process_decode_dream`)
*   **Problem**: SNN spikes are unintelligible to the Validator.
*   **Solution**: The system calculates the **Average Prototype Vector** of all firing neurons.
*   **Result**: It maps this vector back to physical coordinates `(x, y)` using Heuristic Decoding (Argmax). The agent "sees" where it is in the dream.

### C. Validation (`process_validate_and_reward`)
The agent consults its **World Model (Beliefs)** to judge the dream.
*   **Scenario 1: Novelty (Explore)** -> `Reward +0.5`.
*   **Scenario 2: Danger/Impossible (Lava/Walls)** -> `Punishment -1.0`.
*   **Outcome**: It injects a synthetic `td_error`, triggering STDP to learn *without* physical consequences.

## 3.2 Defense Mechanisms (The Immune System)
To prevent "Epileptic Seizures" (Runaway Feedback Loops) common in Recurrent SNNs.

### Layer 1: Self-Regulation (Fast Homeostasis)
*   **Process**: `process_dream_learning`
*   **Logic**: Proportional Control (Heuristic).
    *   If `Fire_Rate > Nightmare_Threshold`: **Aggressively Increase Thresholds**.
    *   Effect: Makes neurons "numb" immediately.

### Layer 2: Emergency Brake (Sanity Check)
*   **Process**: `process_dream_sanity_check`
*   **Logic**: If Layer 1 failed and the system is still in `Nightmare` state from the previous tick:
    *   **Action**: `Spike_Queue.clear()`
    *   **Effect**: Total blackout. Stops the seizure instantly.

## 3.3 The "Groggy" Effect (Wake-up Persistence)
An emergent phenomenon of State Persistence.

### The Phenomenon
1.  **Nightmare**: Agent raises thresholds significantly (`+0.05`) to suppress fear/overload.
2.  **Wake Up**: The system switches workflow (`agent_main.yaml`) **without resetting** neuron states.
3.  **Result**: The agent enters reality with "High Defense" (High Thresholds). It is unresponsive and sluggish.

### The Recovery
*   **Mechanism**: `process_meta_homeostasis_fixed` (PID Controller).
*   **Rate**: Very slow (`0.0001` per step).
*   **Duration**: It takes hundreds of ticks for the agent to "sober up" and return to peak performance.

## 3.4 Applications
1.  **Safety Training**: Learning to avoid "Lava" in dreams prevents burning in reality.
2.  **Prospective Memory**: Tagging synapses during dreams (`trace_slow`) primes them for rapid "One-Shot Learning" when the event actually occurs in reality (Dejà vu).
