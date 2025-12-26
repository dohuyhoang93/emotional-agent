# Chapter 6: Population & Social Evolution

**Scope**: From Individual Intelligence to Collective Wisdom. How agents share knowledge and evolve as a species.

## 6.1 Memetic Transfer (The Viral Mechanism)
**Processes**: `process_extract_top_synapses` & `process_inject_viral_synapses` (in `snn_social_theus.py`)

Knowledge in Theus is treated like a **Virus** (Method: "Viral Synaptic Transfer").
*   **Export (The Carrier)**:
    *   Each agent periodically scans its brain for "Elite Synapses" (High Weight + High Confidence).
    *   It packages these into a digital packet called a **Meme**.
*   **Import (The Infection)**:
    *   Broadcasters transmit Memes to nearby agents.
    *   Receivers inject these Memes into their own synaptic web.

## 6.2 Social Immunology (The Quarantine Sandbox)
**Process**: `process_quarantine_validation` (in `snn_social_quarantine_theus.py`)

To prevent "Bad Ideas" (Misinformation/Malware) from destroying the brain, the agent operates on a **Zero-Trust** model.
*   **The Sandbox (Shadow Synapses)**:
    *   Incoming Memes are NOT allowed to fire motors. They are placed in **Shadow Mode**.
    *   They typically run principally in parallel with Native synapses but are disconnected from the output.
*   **Evaluation (The Trial)**:
    *   The system compares predictions: `Error_Native` vs `Error_Shadow`.
    *   **Promotion**: If `Error_Shadow < Error_Native` consistently -> The Meme replaces the Native synapse (Learning successful).
    *   **Rejection**: If `Error_Shadow > Error_Native` -> The Meme is deleted.
*   **Blacklisting**:
    *   If a source agent repeatedly sends "Bad Memes", it is added to a `Blacklist`. The agent stops listening to that neighbor.

## 6.3 Cultural Revolution (Evolution of the Species)
**Process**: `process_revolution_protocol` (in `snn_advanced_features_theus.py`)

Evolution doesn't just happen at the individual level; it happens to the **Baseline (Archetype)**.
*   **Trigger**:
    *   The system monitors the Global Population Performance.
    *   Condition: If >60% of the current population outperforms the original `Ancestor` (Default Weights).
*   **The Revolution**:
    1.  **Select Elite**: Identify the Top 10% performing agents.
    2.  **Synthesize**: Compute the average weights of this elite group.
    3.  **Overwrite**: This new weight configuration becomes the **New Ancestor**.
*   **Effect**: All future agents spawned will start from this superior baseline. The species has "leveled up".

## 6.4 Conclusion
Theus agents form a **Complex Adaptive System**.
*   **Individuals** innovate via Dream Learning & STDP.
*   **Society** filters innovations via Quarantine & Memetics.
*   **Species** locks in progress via Revolution.
