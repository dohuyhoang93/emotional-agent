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


class ExperimentLogger:
    """
    Structured logger for experiments.
    
    Logs to:
    - Console (INFO+)
    - File (DEBUG+)
    - Metrics file (JSON)
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
        self.log_dir.mkdir(exist_ok=True)
        
        # Metrics storage
        self.metrics_history = []
        
        # Setup logging
        self.logger = logging.getLogger(experiment_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
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
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        self.logger.info(f"Experiment '{experiment_name}' started")
    
    def log_episode(self, episode: int, metrics: Dict[str, Any]):
        """
        Log episode metrics.
        
        Args:
            episode: Episode number
            metrics: Episode metrics
        """
        self.logger.info(
            f"Episode {episode:3d}: "
            f"avg_reward={metrics.get('avg_reward', 0):.4f}, "
            f"agents={len(metrics.get('agent_rewards', []))}"
        )
        
        # Store metrics
        self.metrics_history.append({
            'episode': episode,
            'timestamp': datetime.now().isoformat(),
            **metrics
        })
    
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
        """Save metrics to JSON file."""
        metrics_file = self.log_dir / f"{self.experiment_name}_metrics.json"
        
        with open(metrics_file, 'w') as f:
            json.dump({
                'experiment': self.experiment_name,
                'start_time': self.start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_seconds': (datetime.now() - self.start_time).total_seconds(),
                'metrics': self.metrics_history
            }, f, indent=2)
        
        self.logger.info(f"Metrics saved to {metrics_file}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get experiment summary."""
        if not self.metrics_history:
            return {}
        
        avg_rewards = [m.get('avg_reward', 0) for m in self.metrics_history]
        
        return {
            'total_episodes': len(self.metrics_history),
            'avg_reward': sum(avg_rewards) / len(avg_rewards),
            'best_reward': max(avg_rewards),
            'worst_reward': min(avg_rewards),
            'duration_seconds': (datetime.now() - self.start_time).total_seconds()
        }
