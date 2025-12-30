# Experimental Features

This directory contains **experimental features** that are:
- ✅ Fully implemented code
- ⚠️ Not integrated into production workflows
- 🔬 Under research/evaluation

---

## Features in This Directory

### 1. Safety Triggers (`snn_safety_theus.py`)

**Status**: 90% Complete (Implemented but not integrated)  
**Author**: Do Huy Hoang  
**Date**: 2025-12-29

**Description**: Advanced safety monitoring system with 3 trigger types:
1. **Bottom-Up Override**: Emergency brake when TD-error is high
2. **Saccadic Reset**: Context switch detection when action changes
3. **Curiosity Veto**: Alert when novelty is very high

**Why Experimental**:
- Overlaps with existing safety mechanisms (Hysteria Dampener, Intrinsic Reward)
- Uncertain value-add vs current implementation
- Needs research to determine if integration is beneficial

**Potential Use Cases**:
- Saccadic Reset could be useful for attention management
- Bottom-Up Override might provide additional safety layer
- Research needed to validate benefits

**To Integrate**:
```yaml
# Add to workflows/agent_main.yaml
- process: monitor_safety_triggers
  description: "Phase 11: Safety Monitoring"
```

---

### 2. Imagination Processes (`snn_imagination_theus.py`)

**Status**: 80% Complete (Code exists but not used)  
**Author**: Do Huy Hoang  
**Date**: 2025-12-25

**Description**: Offline learning through imagination/replay:
1. **`process_imagination_loop`**: Replay memories without sensory input
2. **`process_dream_learning`**: Adjust thresholds based on dream quality

**Why Experimental**:
- Requires separate workflow (imagination mode)
- Uncertain performance benefit vs existing dream cycle
- Needs extensive testing and validation

**Potential Use Cases**:
- Offline learning during idle time
- Memory consolidation enhancement
- Transfer learning between tasks

**To Integrate**:
```yaml
# Create workflows/agent_imagination.yaml
name: "Imagination Loop"
steps:
  - process_imagination_loop
  - process_snn_cycle
  - process_dream_learning
```

---

### 3. Dream Sanity Check (`p_dream_sanity.py`)

**Status**: 50% Complete (Partial implementation)  
**Author**: Do Huy Hoang  
**Date**: 2025-12-26

**Description**: Validate dream against beliefs, suppress nightmares
- Detects nightmare type and suppresses by clearing spike queue
- Intended for world model validation

**Why Experimental**:
- Overlaps with `process_dream_coherence_reward` (already detects bad dreams)
- Overlaps with `process_hysteria_dampener` (already suppresses runaway activity)
- Incomplete world model integration
- Redundant with existing safety mechanisms

**Current Logic**:
```python
if metrics.get('dream_type') == 'nightmare':
    metrics['dream_suppressed'] = 1
    spike_queue.clear()  # Suppress
```

**Missing**:
- Belief consistency checking
- Switch state validation
- Sophisticated world model integration

**Recommendation**: Needs research to justify vs existing mechanisms

---

### 4. Dream Validator (`p_dream_validator.py`)

**Status**: 100% Complete (Not integrated - Phase 13)  
**Author**: Do Huy Hoang  
**Date**: 2025-12-26

**Description**: Validate decoded dream states + inject synthetic rewards
- Part of **Phase 13: Semantic Dream Learning**
- Validates dream (x, y) against world model
- Injects synthetic TD-error for STDP

**Features**:
1. ✅ Boundary validation (x, y in [0-7])
2. ✅ Danger zone detection (lava at 3,3)
3. ✅ Exploration bonus (edges)
4. ✅ Synthetic reward injection

**Why Experimental**:
- Advanced feature (Phase 13)
- Requires world model (`believed_switch_states`)
- Needs validation of effectiveness

**Potential Value**:
- Could improve dream quality
- Teaches agent to avoid dangers in dreams
- Reinforces exploration patterns

**To Integrate**:
```yaml
# Add to workflows/agent_dream.yaml after decode_dream
- process_decode_dream
- process_validate_and_reward  # ← Add this
- process_stdp_3factor
```

---

## Guidelines for Experimental Features

### When to Add Features Here
- ✅ Code is complete and functional
- ✅ Feature is not critical for production
- ✅ Needs research/validation before integration
- ✅ May have overlap with existing mechanisms

### When to Move to Production
- ✅ Research validates clear benefit
- ✅ No significant overlap with existing features
- ✅ Tested and proven stable
- ✅ Integrated into workflows

### When to Archive/Remove
- ❌ Research shows no benefit
- ❌ Redundant with existing features
- ❌ Performance overhead not justified

---

## Research Status

| Feature | Research Priority | Next Steps |
|---------|------------------|------------|
| **Safety Triggers** | 🟡 Medium | Test Saccadic Reset in complex environments |
| **Imagination** | 🟡 Medium | Compare learning with/without imagination |
| **Dream Sanity** | 🟢 Low | Evaluate vs coherence_reward (likely redundant) |
| **Dream Validator** | 🟠 High | Test Phase 13 semantic learning benefits |

---

## Notes

- All code in this directory is **production-quality** but **not production-integrated**
- Features can be imported and tested independently
- See `dream_system_audit.md` and `gap_analysis_report.md` for detailed analysis

---

**Last Updated**: 2025-12-30  
**Maintained by**: EmotionAgent Team
