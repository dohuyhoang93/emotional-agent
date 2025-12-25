"""
Performance Monitor
===================
Track performance metrics for experiments.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import time
import psutil
import numpy as np
from typing import Dict, Any, List


class PerformanceMonitor:
    """
    Monitor performance metrics.
    
    Tracks:
    - Episode duration
    - Memory usage
    - SNN metrics
    - RL metrics
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.episode_times: List[float] = []
        self.memory_usage: List[float] = []
        self.start_time: float = None
        self.process = psutil.Process()
    
    def start_episode(self):
        """Start episode timer."""
        self.start_time = time.time()
    
    def end_episode(self):
        """End episode and record metrics."""
        if self.start_time is None:
            return
        
        # Duration
        duration = time.time() - self.start_time
        self.episode_times.append(duration)
        
        # Memory usage (MB)
        memory_mb = self.process.memory_info().rss / 1024 / 1024
        self.memory_usage.append(memory_mb)
        
        self.start_time = None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        if not self.episode_times:
            return {
                'avg_episode_time': 0.0,
                'total_time': 0.0,
                'avg_memory_mb': 0.0,
                'peak_memory_mb': 0.0
            }
        
        return {
            'avg_episode_time': np.mean(self.episode_times),
            'min_episode_time': min(self.episode_times),
            'max_episode_time': max(self.episode_times),
            'total_time': sum(self.episode_times),
            'avg_memory_mb': np.mean(self.memory_usage),
            'peak_memory_mb': max(self.memory_usage),
            'episodes_per_second': len(self.episode_times) / sum(self.episode_times)
        }
    
    def get_current_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
