# Implementation Plan: Delta Replay (Option A) for Zero Trust Memory

**Ngày:** 2026-01-28  
**Phiên bản mục tiêu:** Theus v3.1.0  
**Cơ sở:** [DELTA_VS_SHADOW_ANALYSIS.md](file:///C:/Users/dohoang/projects/EmotionAgent/Documents/ADR/V3/DELTA_VS_SHADOW_ANALYSIS.md)

---

## User Review Required

> [!IMPORTANT]
> **Behavioral Change**: Sau khi triển khai, proxy mutations (`ctx.domain['key'] = val`) sẽ được commit thông qua **delta replay** thay vì shadow copy. Điều này:
> - ✅ Không thay đổi API công khai
> - ✅ Không ảnh hưởng đến Heavy Zone
> - ⚠️ Yêu cầu `delta_log` phải chính xác (đã được test)

---

## Proposed Changes

### Phase 1: Core Infrastructure (Rust)

#### 1.1 [MODIFY] [engine.rs](file:///C:/Users/dohoang/projects/EmotionAgent/theus_framework/src/engine.rs)

**Task:** Implement `build_pending_from_deltas()` method

```rust
/// Replay delta_log entries onto a fresh copy of State
fn build_pending_from_deltas(&self, py: Python) -> PyResult<PyObject> {
    let result = PyDict::new_bound(py);
    let delta_log = self.delta_log.lock().unwrap();
    
    for entry in delta_log.iter() {
        // Parse path and set nested value
        set_nested_value(py, &result, &entry.path, &entry.value)?;
    }
    
    Ok(result.unbind().into_py(py))
}
```

**Affected lines:** ~400-450 (new method after `get_shadow_updates`)

---

#### 1.2 [NEW] [structures_helper.rs](file:///C:/Users/dohoang/projects/EmotionAgent/theus_framework/src/structures_helper.rs)

**Task:** Implement robust `set_nested_value()` for path parsing

```rust
/// Set value at nested path like "domain.users[0].name"
pub fn set_nested_value(
    py: Python, 
    root: &Bound<'_, PyDict>,
    path: &str, 
    value: &Option<Py<PyAny>>
) -> PyResult<()> {
    let segments = parse_path_segments(path);
    // Navigation + creation logic
    // Handle both dict keys and list indices
}

/// Parse "domain.users[0].name" -> ["domain", "users", "[0]", "name"]
fn parse_path_segments(path: &str) -> Vec<PathSegment> {
    // Regex or manual parsing
}

enum PathSegment {
    Key(String),
    Index(usize),
}
```

---

#### 1.3 [MODIFY] [proxy.rs](file:///C:/Users/dohoang/projects/EmotionAgent/theus_framework/src/proxy.rs)

**Task:** Ensure `__setitem__` logs complete delta with cloned value

```rust
// Line ~237: Ensure value is cloned, not referenced
if let Ok(tx_bound) = tx.bind(py).getattr("log_delta") {
    let cloned_value = value.clone_ref(py);  // IMPORTANT: Clone!
    let _ = tx_bound.call1((full_path, old_val, cloned_value));
}
```

**Risk:** Low - already logging, just verify clone behavior.

---

### Phase 2: Python Adapter  

#### 2.1 [MODIFY] [engine.py](file:///C:/Users/dohoang/projects/EmotionAgent/theus_framework/theus/engine.py)

**Task:** Replace `get_shadow_updates()` with `build_pending_from_deltas()`

```python
# Line ~345-347: Change from shadow to delta replay
# Before:
# shadow_data = tx.get_shadow_updates()

# After:
pending_data = tx.build_pending_from_deltas()
self._core.compare_and_swap(
    start_version, 
    data=pending_data,  # Delta-replayed data
    heavy=tx.pending_heavy, 
    signal=tx.pending_signal
)
```

---

### Phase 3: Cleanup (Optional)

#### 3.1 [MODIFY] [engine.rs](file:///C:/Users/dohoang/projects/EmotionAgent/theus_framework/src/engine.rs)

**Task:** Remove obsolete `path_to_shadow` and related code

```rust
// Remove from Transaction struct:
// pub path_to_shadow: Arc<Mutex<HashMap<String, PyObject>>>

// Remove from constructors and get_shadow()
```

**Note:** Keep `shadow_cache` for CoW isolation during process execution.

---

## Impact Analysis

### Affected Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    IMPACT DIAGRAM                                │
│                                                                  │
│  ┌─────────────┐                                                 │
│  │ @process    │                                                 │
│  │ functions   │──No change──────────────────────────────────▶  │
│  └─────────────┘                                                 │
│                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐       │
│  │ ctx.domain  │───▶│ Supervisor   │───▶│ delta_log     │       │
│  │ mutations   │    │ Proxy        │    │ (unchanged)   │       │
│  └─────────────┘    └──────────────┘    └───────────────┘       │
│                            │                   │                 │
│                            │                   ▼                 │
│                            │         ┌─────────────────┐        │
│                            │         │ build_pending   │◀─ NEW  │
│                            │         │ _from_deltas()  │        │
│                            │         └─────────────────┘        │
│                            │                   │                 │
│                            ▼                   ▼                 │
│                     ┌──────────────────────────────┐            │
│                     │ compare_and_swap()           │            │
│                     │ (unchanged API)              │            │
│                     └──────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Backward Compatibility

| Component | Impact | Notes |
|-----------|--------|-------|
| **@process functions** | ✅ None | API unchanged |
| **tx.update()** | ✅ None | Still works, goes to pending_data |
| **ctx.domain['x'] = y** | ✅ None | Still works, now via delta replay |
| **Heavy Zone** | ✅ None | Separate path, unaffected |
| **EmotionAgent** | ✅ None | All processes unchanged |
| **Third-party apps** | ✅ None | Public API unchanged |

### Performance Impact

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Memory per Transaction** | O(shadow_size) | O(delta_count) | ⬇️ Better |
| **Commit latency** | O(1) shadow swap | O(n) delta replay | ⬆️ Slightly slower |
| **Rollback latency** | O(1) | O(1) | = Same |

**Net Effect:** Better memory, slightly slower commit for many mutations.

---

## Verification Plan

### Test 1: Basic Delta Replay
```python
@process
def test_basic(ctx):
    ctx.domain['new_key'] = 'new_value'

# Assert: state['domain']['new_key'] == 'new_value'
```

### Test 2: Nested Path Replay
```python
@process  
def test_nested(ctx):
    ctx.domain['users'][0]['name'] = 'Updated'

# Assert: state['domain']['users'][0]['name'] == 'Updated'
```

### Test 3: Rollback (Crash Recovery)
```python
@process
def test_crash(ctx):
    ctx.domain['should_not_exist'] = 'value'
    raise ValueError("Intentional crash")

# Assert: 'should_not_exist' NOT in state['domain']
```

### Test 4: Heavy Zone Unaffected
```python
@process
def test_heavy(ctx):
    ctx.heavy_weights[0] = large_tensor  # Direct, no delta

# Assert: heavy_weights updated immediately (no rollback)
```

---

## Implementation Checklist

- [ ] **1.1** Implement `build_pending_from_deltas()` in `engine.rs`
- [ ] **1.2** Implement `set_nested_value()` in `structures_helper.rs`
- [ ] **1.3** Verify `proxy.rs` delta logging clones values
- [ ] **2.1** Update `engine.py` commit logic
- [ ] **3.1** Remove `path_to_shadow` (cleanup)
- [ ] **Test** Run `verify_universal_mutation.py` - all tests pass
- [ ] **Version** Bump to v3.1.0
- [ ] **Docs** Update tutorial Chapter 12 (Zero Trust)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Path parsing bugs | Comprehensive unit tests for edge cases |
| Performance regression | Benchmark before/after |
| Breaking existing apps | Backward compat tests |

---

## Timeline Estimate

| Task | Effort |
|------|--------|
| Phase 1 (Rust) | ~2 hours |
| Phase 2 (Python) | ~30 mins |
| Phase 3 (Cleanup) | ~30 mins |
| Testing | ~1 hour |
| **Total** | **~4 hours** |
