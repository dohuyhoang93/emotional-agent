# Chapter 6: Population & Social Evolution

**Scope**: From Individual Intelligence to Collective Wisdom. How agents share knowledge and evolve as a species.

> [!IMPORTANT]
> **Implementation Status**: All social learning and evolution mechanisms are **FULLY IMPLEMENTED** as of 2025-12-30.

---

## 6.1 Memetic Transfer (The Viral Mechanism)

**Processes**: `process_extract_top_synapses` & `process_inject_viral_synapses`  
**File**: `src/processes/snn_social_theus.py`  
**Status**: ✅ **IMPLEMENTED**

Knowledge in Theus is treated like a **Virus** (Method: "Viral Synaptic Transfer").

### Export (The Carrier)

*   Each agent periodically scans its brain for "Elite Synapses" (High Weight + High Confidence).
*   It packages these into a digital packet called a **Meme**.

**Implementation**:
```python
def process_extract_top_synapses(ctx: SystemContext):
    """Extract elite synapses for sharing."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    # Filter criteria
    min_weight = 0.7
    min_confidence = 0.6
    
    elite_synapses = []
    for synapse in snn_ctx.domain_ctx.synapses:
        if (synapse.weight >= min_weight and 
            synapse.confidence >= min_confidence):
            elite_synapses.append({
                'pre_id': synapse.pre_neuron_id,
                'post_id': synapse.post_neuron_id,
                'weight': synapse.weight,
                'confidence': synapse.confidence,
                'source_agent': ctx.domain_ctx.agent_id
            })
    
    # Package as meme
    ctx.domain_ctx.outgoing_memes = elite_synapses
```

### Import (The Infection)

*   Broadcasters transmit Memes to nearby agents.
*   Receivers inject these Memes into their own synaptic web.

**Implementation**:
```python
def process_inject_viral_with_quarantine(ctx: SystemContext):
    """Inject foreign synapses with quarantine."""
    snn_ctx = ctx.domain_ctx.snn_context
    incoming_memes = ctx.domain_ctx.incoming_memes
    
    for meme in incoming_memes:
        # Create shadow synapse (quarantined)
        shadow_synapse = SynapseState(
            synapse_id=generate_id(),
            pre_neuron_id=meme['pre_id'],
            post_neuron_id=meme['post_id'],
            weight=meme['weight'],
            synapse_type='shadow',  # NOT native
            source_agent_id=meme['source_agent'],
            confidence=meme['confidence'],
            quarantine_time=0  # Start quarantine
        )
        
        snn_ctx.domain_ctx.synapses.append(shadow_synapse)
```

**Hyperparameters**:
- `min_weight_export`: 0.7 (elite threshold)
- `min_confidence_export`: 0.6
- `max_memes_per_agent`: 50

---

## 6.2 Social Immunology (The Quarantine Sandbox)

**Process**: `process_quarantine_validation`  
**File**: `src/processes/snn_social_quarantine_theus.py`  
**Status**: ✅ **IMPLEMENTED**

To prevent "Bad Ideas" (Misinformation/Malware) from destroying the brain, the agent operates on a **Zero-Trust** model.

### The Sandbox (Shadow Synapses)

*   Incoming Memes are NOT allowed to fire motors. They are placed in **Shadow Mode**.
*   They run in parallel with Native synapses but are disconnected from the output.

### Evaluation (The Trial)

*   The system compares predictions: `Error_Native` vs `Error_Shadow`.
*   **Promotion**: If `Error_Shadow < Error_Native` consistently -> The Meme replaces the Native synapse (Learning successful).
*   **Rejection**: If `Error_Shadow > Error_Native` -> The Meme is deleted.

**Implementation**:
```python
def process_quarantine_validation(ctx: SystemContext):
    """Validate shadow synapses via performance comparison."""
    snn_ctx = ctx.domain_ctx.snn_context
    
    validation_threshold = 10  # Steps in quarantine
    promotion_threshold = 0.8  # Performance ratio
    
    for synapse in list(snn_ctx.domain_ctx.synapses):
        if synapse.synapse_type != 'shadow':
            continue
        
        synapse.quarantine_time += 1
        
        if synapse.quarantine_time < validation_threshold:
            continue
        
        # Compare with native synapse (same pre/post)
        native = find_native_synapse(
            snn_ctx, 
            synapse.pre_neuron_id, 
            synapse.post_neuron_id
        )
        
        if native is None:
            # No competition, promote
            synapse.synapse_type = 'native'
            continue
        
        # Performance comparison
        shadow_score = synapse.validation_score
        native_score = native.validation_score
        
        if shadow_score > native_score * promotion_threshold:
            # Shadow wins: Replace native
            snn_ctx.domain_ctx.synapses.remove(native)
            synapse.synapse_type = 'native'
        else:
            # Native wins: Delete shadow
            snn_ctx.domain_ctx.synapses.remove(synapse)
```

### Blacklisting

*   If a source agent repeatedly sends "Bad Memes", it is added to a `Blacklist`. The agent stops listening to that neighbor.

**Implementation**:
```python
# Track failed memes per source
if synapse_rejected:
    source_id = synapse.source_agent_id
    failure_count[source_id] = failure_count.get(source_id, 0) + 1
    
    if failure_count[source_id] > blacklist_threshold:
        blacklist.add(source_id)
        metrics['blacklisted_agents'] = len(blacklist)
```

**Hyperparameters**:
- `validation_threshold`: 10 steps
- `promotion_threshold`: 0.8 (80% of native performance)
- `blacklist_threshold`: 5 (failed memes)

---

## 6.3 Cultural Revolution (Evolution of the Species)

**Process**: `process_revolution_protocol`  
**File**: `src/processes/snn_advanced_features_theus.py::process_revolution_protocol` (Lines 427-566)  
**Status**: ✅ **IMPLEMENTED**

Evolution doesn't just happen at the individual level; it happens to the **Baseline (Archetype)**.

### Trigger

*   The system monitors the Global Population Performance.
*   Condition: If >60% of the current population outperforms the original `Ancestor` (Default Weights).

### The Revolution

1.  **Select Elite**: Identify the Top 10% performing agents.
2.  **Synthesize**: Compute the average weights of this elite group to create a new **Ancestor**.
3.  **Active Assimilation** (`process_assimilate_ancestor`):
    *   **Mechanism**: All active agents immediately begin to "download" the new Ancestor's weights.
    *   **Diversity Noise**: A small Gaussian noise is added during download to maintain population diversity.
    *   **Protection Policy**: Synapses marked as **SOLID** (Long-term Memory) are **Protected** and NOT overwritten. Only "Fluid" (weak/new) connections are replaced by the Ancestor's wisdom.
*   **Effect**: The population "raises its floor" to the level of the elite, while retaining individual specialized knowledge.

**Implementation** (`process_revolution_protocol`):
```python
def process_revolution_protocol(
    snn_ctx: SNNSystemContext,
    rl_ctx: SystemContext = None,
    population_contexts: List[SNNSystemContext] = None
):
    """Cultural Evolution: Update ancestor when population excels."""
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    # Single-agent mode: Skip
    if population_contexts is None or len(population_contexts) <= 1:
        return
    
    # Check revolution condition
    current_baseline = domain.ancestor_baseline_reward
    outperform_count = sum(
        1 for p in domain.population_performance
        if p > current_baseline
    )
    outperform_ratio = outperform_count / len(domain.population_performance)
    
    if outperform_ratio > global_ctx.revolution_threshold:  # 0.6
        domain.revolution_triggered = True
        
        # Select elite (top 10%)
        all_perfs = [
            (i, np.mean(ctx.domain_ctx.population_performance[-100:]))
            for i, ctx in enumerate(population_contexts)
        ]
        all_perfs.sort(key=lambda x: x[1], reverse=True)
        elite_count = max(1, int(len(all_perfs) * global_ctx.top_elite_percent))
        elite_indices = [idx for idx, _ in all_perfs[:elite_count]]
        
        # Compute new ancestor (average elite weights)
        new_ancestor = {}
        for syn_id in domain.ancestor_weights.keys():
            elite_weights = []
            for idx in elite_indices:
                elite_ctx = population_contexts[idx]
                for syn in elite_ctx.domain_ctx.synapses:
                    if syn.synapse_id == syn_id:
                        elite_weights.append(syn.weight)
            
            if elite_weights:
                new_ancestor[syn_id] = np.mean(elite_weights)
        
        # Update ancestor
        if new_ancestor:
            domain.ancestor_weights = new_ancestor
            domain.metrics['revolution_count'] += 1
        
        # Reset history & update baseline
        domain.population_performance = []
        new_baseline = np.mean([p for i, p in all_perfs[:elite_count]])
        domain.ancestor_baseline_reward = new_baseline
```

**Implementation** (`process_assimilate_ancestor`):
```python
def process_assimilate_ancestor(ctx: SystemContext):
    """Apply Ancestor Knowledge with Noise."""
    snn_ctx = ctx.domain_ctx.snn_context
    domain = snn_ctx.domain_ctx
    global_ctx = snn_ctx.global_ctx
    
    ancestor = domain.ancestor_weights
    if not ancestor:
        return
    
    alpha = global_ctx.assimilation_rate  # 0.05
    noise_std = global_ctx.diversity_noise  # 0.02
    
    for synapse in domain.synapses:
        # PROTECT SOLID KNOWLEDGE
        if synapse.commit_state == COMMIT_STATE_SOLID:
            continue  # Skip protected synapses
        
        if synapse.synapse_id in ancestor:
            target_w = ancestor[synapse.synapse_id]
            
            # Soft Update
            new_w = (1.0 - alpha) * synapse.weight + alpha * target_w
            
            # Diversity Noise
            noise = np.random.randn() * noise_std
            new_w += noise
            
            # Clip
            synapse.weight = np.clip(new_w, 0.0, 1.0)
```

**Hyperparameters**:
- `revolution_threshold`: 0.6 (60% outperform)
- `top_elite_percent`: 0.1 (top 10%)
- `revolution_window`: 1000 (cycles)
- `assimilation_rate`: 0.05 (5% blend)
- `diversity_noise`: 0.02 (2% std)

**Formula**:
```
w_new = (1 - α) * w_current + α * w_ancestor + N(0, σ)

where:
  α = assimilation_rate (0.05)
  σ = diversity_noise (0.02)
  SOLID synapses are protected (skip)
```


---

## 6.4 Conclusion

Theus agents form a **Complex Adaptive System**.

*   **Individuals** innovate via Dream Learning & STDP.
*   **Society** filters innovations via Quarantine & Memetics.
*   **Species** locks in progress via Revolution (planned).

### Multi-Level Learning

```
Individual Level (Every Step):
├─ STDP: Temporal associations
├─ Clustering: Semantic organization
└─ 3-Factor: Reward-driven plasticity

Social Level (Periodic):
├─ Memetic Transfer: Share elite synapses
├─ Quarantine: Validate foreign knowledge
└─ Blacklist: Filter bad sources

Population Level (Planned):
└─ Revolution: Synthesize collective wisdom
```

---

## 6.5 Implementation Status Summary

| Feature | Status | File | Notes |
|---------|--------|------|-------|
| **Memetic Export** | ✅ Implemented | `snn_social_theus.py` | Extract elite synapses |
| **Memetic Import** | ✅ Implemented | `snn_social_theus.py` | Inject with quarantine |
| **Quarantine Validation** | ✅ Implemented | `snn_social_quarantine_theus.py` | Shadow synapse trial |
| **Blacklisting** | ✅ Implemented | `snn_social_quarantine_theus.py` | Filter bad sources |
| **Revolution Protocol** | ✅ Implemented | `snn_advanced_features_theus.py` | Population evolution |
| **Ancestor Assimilation** | ✅ Implemented | `snn_advanced_features_theus.py` | Download collective wisdom |

---

## 6.6 Hyperparameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| `min_weight_export` | 0.7 | Elite synapse threshold |
| `min_confidence_export` | 0.6 | Confidence threshold |
| `max_memes_per_agent` | 50 | Export limit |
| `validation_threshold` | 10 | Quarantine duration (steps) |
| `promotion_threshold` | 0.8 | Shadow must be 80% of native |
| `blacklist_threshold` | 5 | Failed memes before blacklist |
| `revolution_trigger` | 0.6 | 60% outperform ancestor |
| `elite_ratio` | 0.1 | Top 10% for synthesis |

---

> [!NOTE]
> **Related Chapters**:
> - Chapter 2: Learning Mechanisms (STDP, Commitment)
> - Chapter 5: Safety and Homeostasis (Neural Darwinism)
> - Chapter 7: Persistence and Monitoring (Multi-agent coordination)
