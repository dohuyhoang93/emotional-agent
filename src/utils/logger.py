"""
Experiment Logger
==================
Structured logging for multi-agent experiments.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
import numpy as np


class ExperimentLogger:
    """
    Structured logger for experiments (Optimized for Stability).
    
    Logs to:
    - Console (INFO+)
    - File (DEBUG+)
    - Metrics file (.jsonl) - Append only to prevent data loss and reduce memory usage.
    """
    
    def __init__(self, experiment_name: str, log_dir: str = "logs"):
        """
        Initialize logger.
        
        Args:
            experiment_name: Name of experiment
            log_dir: Directory for log files
        """
        self.experiment_name = experiment_name
        self.start_time = datetime.now()
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True) # Ensure parents exist
        
        # Metrics file (JSON Lines for robustness)
        self.metrics_file = self.log_dir / "metrics.jsonl"
        
        # Setup logging
        self.logger = logging.getLogger(experiment_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to prevent duplication
        if self.logger.hasHandlers():
            self.logger.handlers.clear()
        
        # Console handler (INFO+)
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console.setFormatter(console_formatter)
        self.logger.addHandler(console)
        
        # File handler (DEBUG+)
        log_file = self.log_dir / f"{experiment_name}_{self.start_time:%Y%m%d_%H%M%S}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"Experiment '{experiment_name}' started. Metrics: {self.metrics_file}")
    
    def log_episode(self, episode: int, metrics: Dict[str, Any]):
        """
        Log episode metrics (Atomic Append).
        
        Args:
            episode: Episode number
            metrics: Episode metrics
        """
        self.logger.info(
            f"Episode {episode:3d}: "
            f"agents={len(metrics.get('agent_rewards', []))} "
            f"R={metrics.get('avg_reward', 0):.2f}"
        )
        
        # Construct Entry
        entry = {
            'episode': episode,
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        # Append to JSONL file immediately
        try:
            # Convert Frozen types to native Python types for JSON serialization
            def to_serializable(obj):
                """Recursively convert Frozen types to native Python types."""
                if isinstance(obj, (np.integer, np.floating)):
                    return obj.item()
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes)):
                    if hasattr(obj, 'items'):  # Dict-like (FrozenDict)
                        return {k: to_serializable(v) for k, v in obj.items()}
                    else:  # List-like (FrozenList, tuple)
                        return [to_serializable(item) for item in obj]
                return obj
            
            serializable_entry = to_serializable(entry)
            
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(serializable_entry) + '\n')
        except Exception as e:
            self.logger.error(f"Failed to write metrics for Ep {episode}: {e}")
            
    def log_social_learning(self, stats: Dict[str, Any]):
        """Log social learning event."""
        self.logger.info(
            f"📚 Social Learning: "
            f"transfers={stats.get('total_transfers', 0)}, "
            f"synapses={stats.get('total_synapses', 0)}"
        )
    
    def log_revolution(self, stats: Dict[str, Any]):
        """Log revolution event."""
        self.logger.warning(
            f"🔥 REVOLUTION #{stats.get('total_revolutions', 0)}: "
            f"elite={stats.get('last_revolution', {}).get('elite_ids', [])}"
        )
    
    def log_error(self, error: Exception, context: str = ""):
        """Log error with context."""
        self.logger.error(f"Error in {context}: {error}", exc_info=True)
    
    def save_metrics(self):
        """No-op for JSONL logger (saved continuously)."""
        pass
    
    def get_summary(self) -> Dict[str, Any]:
        """Get experiment summary by reading JSONL (Optional/Lazy)."""
        # Note: Avoid reading full file if large. Just return basic stats.
        return {
             'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
             'status': 'Running'
        }
