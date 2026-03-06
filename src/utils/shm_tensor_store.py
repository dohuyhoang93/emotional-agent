"""
ShmTensorStore — Dict-like wrapper cho Theus HeavyZoneAllocator.
================================================================
Cho phép code hiện tại dùng `domain.heavy_tensors[key]` giống dict
bình thường, nhưng backing bằng SharedMemory (zero-copy).

Author: Do Huy Hoang
Date: 2026-03-05
"""
import numpy as np
from typing import Any, Optional


class ShmTensorStore(dict):
    """
    Dict-like interface backed by SharedMemory via HeavyZoneAllocator.

    Usage:
        store = ShmTensorStore(allocator, prefix="agent_0")
        store['weights'] = np.zeros((1024, 1024), dtype=np.float32)
        data = store['weights']  # Zero-copy read from SHM

    NOTE: Nếu allocator None hoặc init fail, degrade thành plain dict
    (safety net cho tests và environments thiếu SHM support).
    """

    def __init__(self, allocator=None, prefix: str = ""):
        super().__init__()
        self._allocator = allocator
        self._prefix = prefix
        # NOTE: Track SHM-backed keys riêng biệt vì một số values
        # không phải ndarray (e.g. bool flags như 'use_vectorized_queue')
        self._shm_keys = set()

    def _make_shm_name(self, key: str) -> str:
        """Tạo unique SHM name từ prefix + key."""
        if self._prefix:
            return f"{self._prefix}_{key}"
        return key

    def __setitem__(self, key: str, value: Any):
        """
        Ghi value vào store.
        - ndarray → alloc SHM segment, copy data vào
        - Non-ndarray (bool, int, etc.) → lưu trong dict thường
        """
        if self._allocator is not None and isinstance(value, np.ndarray):
            try:
                shm_name = self._make_shm_name(key)

                if key in self._shm_keys:
                    # NOTE: Key đã tồn tại trong SHM. Nếu shape+dtype match,
                    # ghi đè in-place (zero-alloc). Nếu khác, phải re-alloc.
                    existing = super().__getitem__(key)
                    if (hasattr(existing, 'shape')
                            and existing.shape == value.shape
                            and existing.dtype == value.dtype):
                        existing[:] = value
                        return
                    # Shape/dtype mismatch → fall through to re-alloc

                # Alloc mới
                shm_arr = self._allocator.alloc(
                    shm_name, shape=value.shape, dtype=value.dtype
                )
                shm_arr[:] = value
                super().__setitem__(key, shm_arr)
                self._shm_keys.add(key)
                return
            except Exception:
                # NOTE: SHM alloc thất bại (e.g. FileExistsError khi
                # re-alloc cùng name). Fallback: lưu ndarray thường.
                pass

        # Fallback: plain dict storage (non-ndarray hoặc SHM fail)
        super().__setitem__(key, value)

    def __repr__(self):
        shm_count = len(self._shm_keys)
        total = len(self)
        return (
            f"ShmTensorStore(prefix='{self._prefix}', "
            f"keys={total}, shm_backed={shm_count})"
        )
