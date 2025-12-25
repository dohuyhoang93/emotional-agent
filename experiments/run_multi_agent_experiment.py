"""
Multi-Agent Experiment Runner
==============================
End-to-end experiment runner với full integration.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import sys
sys.path.append('.')

from typing import Dict, Any
from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.coordination.social_learning import SocialLearningManager
from src.coordination.revolution_protocol import RevolutionProtocolManager
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from src.adapters.environment_adapter import EnvironmentAdapter
from src.utils.logger import ExperimentLogger
from src.utils.performance_monitor import PerformanceMonitor
from src.tools.brain_biopsy_theus import BrainBiopsyTheus
from src.utils.snn_persistence import save_snn_agent
from environment import GridWorld


class MultiAgentExperiment:
    """
    End-to-end experiment runner.
    
    Integrates:
    - MultiAgentCoordinator
    - SocialLearningManager
    - RevolutionProtocolManager
    - Logging & Performance Monitoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize experiment.
        
        Args:
            config: Experiment configuration
        """
        self.config = config
        
        # Logger
        self.logger = ExperimentLogger(
            experiment_name=config.get('name', 'multi_agent_experiment')
        )
        
        # Performance monitor
        self.perf_monitor = PerformanceMonitor()
        
        # Create contexts
        global_ctx = GlobalContext(
            initial_needs=config.get('initial_needs', [0.5, 0.5]),
            initial_emotions=config.get('initial_emotions', [0.0, 0.0]),
            total_episodes=config.get('num_episodes', 10),
            max_steps=config.get('max_steps', 50),
            seed=config.get('seed', 42),
            switch_locations={},
            initial_exploration_rate=config.get('exploration_rate', 1.0),
            # Advanced params
            intrinsic_reward_weight=config.get('intrinsic_reward_weight', 0.1),
            use_dynamic_curiosity=config.get('use_dynamic_curiosity', False),
            use_adaptive_fatigue=config.get('use_adaptive_fatigue', False),
            fatigue_growth_rate=config.get('fatigue_growth_rate', 0.001),
            emotional_boost_factor=config.get('emotional_boost_factor', 0.5)
        )
        
        snn_global_ctx = SNNGlobalContext(
            num_neurons=config.get('num_neurons', 50),
            vector_dim=config.get('vector_dim', 16),
            connectivity=config.get('connectivity', 0.15),
            seed=config.get('seed', 42)
        )
        
        # Create coordinator
        self.coordinator = MultiAgentCoordinator(
            num_agents=config.get('num_agents', 5),
            global_ctx=global_ctx,
            snn_global_ctx=snn_global_ctx
        )
        
        # Create managers
        self.social_learning = SocialLearningManager(
            coordinator=self.coordinator,
            elite_ratio=config.get('elite_ratio', 0.2),
            learner_ratio=config.get('learner_ratio', 0.5),
            synapses_per_transfer=config.get('synapses_per_transfer', 10)
        )
        
        self.revolution = RevolutionProtocolManager(
            coordinator=self.coordinator,
            threshold=config.get('revolution_threshold', 0.5),
            window=config.get('revolution_window', 5),
            elite_ratio=config.get('revolution_elite_ratio', 0.1)
        )
        
        # Create environment
        env_config = {
            "initial_needs": config.get('initial_needs', [0.5, 0.5]),
            "initial_emotions": config.get('initial_emotions', [0.0, 0.0]),
            "switch_locations": {},
            "environment_config": {
                "grid_size": config.get('grid_size', 10),
                "max_steps_per_episode": config.get('max_steps', 50),
                "num_agents": config.get('num_agents', 5),
                "start_positions": [[0, i] for i in range(config.get('num_agents', 5))],
                **config.get('environment_config', {})
            }
        }
        self.env = GridWorld(env_config)
        self.adapter = EnvironmentAdapter(self.env)
    
    def run(self, num_episodes: int = None):
        """
        Run experiment.
        
        Args:
            num_episodes: Number of episodes (default from config)
        """
        if num_episodes is None:
            num_episodes = self.config.get('num_episodes', 10)
        
        self.logger.logger.info(f"Starting experiment: {num_episodes} episodes")
        self.logger.logger.info(f"Agents: {self.config.get('num_agents', 5)}")
        
        for episode in range(num_episodes):
            try:
                # Start monitoring
                self.perf_monitor.start_episode()
                
                # Run episode
                metrics = self.coordinator.run_episode(self.env, self.adapter)
                
                # End monitoring
                self.perf_monitor.end_episode()
                
                # Log episode
                self.logger.log_episode(episode, metrics)
                
                # Social learning
                if episode > 0 and episode % self.config.get('social_learning_freq', 5) == 0:
                    self.social_learning.perform_social_learning()
                    stats = self.social_learning.get_transfer_stats()
                    self.logger.log_social_learning(stats)
                
                # Revolution check
                if self.revolution.check_and_execute_revolution():
                    stats = self.revolution.get_revolution_stats()
                    self.logger.log_revolution(stats)
                
                # Brain Biopsy (Start & End only)
                if episode == 0 or episode == num_episodes - 1:
                    self._run_brain_biopsy(episode)
                
            except Exception as e:
                self.logger.log_error(e, f"Episode {episode}")
                continue
        
        # Final summary
        self._print_summary()
        
        # Save metrics
        self.logger.save_metrics()
        
        # Save checkpoints
        self._save_agents(num_episodes)
    
    def _print_summary(self):
        """Print experiment summary."""
        print("\n" + "=" * 60)
        print("EXPERIMENT SUMMARY")
        print("=" * 60)
        
        # Experiment metrics
        summary = self.logger.get_summary()
        print(f"\nExperiment:")
        print(f"  Episodes: {summary.get('total_episodes', 0)}")
        print(f"  Duration: {summary.get('duration_seconds', 0):.2f}s")
        print(f"  Avg Reward: {summary.get('avg_reward', 0):.4f}")
        print(f"  Best Reward: {summary.get('best_reward', 0):.4f}")
        
        # Population metrics
        pop_metrics = self.coordinator.get_population_metrics()
        print(f"\nPopulation:")
        print(f"  Agents: {pop_metrics.get('num_agents', 0)}")
        print(f"  Avg Reward (last 10): {pop_metrics.get('avg_reward', 0):.4f}")
        print(f"  Std Reward: {pop_metrics.get('std_reward', 0):.4f}")
        
        # Social learning
        social_stats = self.social_learning.get_transfer_stats()
        print(f"\nSocial Learning:")
        print(f"  Total Transfers: {social_stats.get('total_transfers', 0)}")
        print(f"  Total Synapses: {social_stats.get('total_synapses', 0)}")
        
        # Revolution
        rev_stats = self.revolution.get_revolution_stats()
        print(f"\nRevolution Protocol:")
        print(f"  Total Revolutions: {rev_stats.get('total_revolutions', 0)}")
        
        # Performance
        perf_stats = self.perf_monitor.get_stats()
        print(f"\nPerformance:")
        print(f"  Avg Episode Time: {perf_stats.get('avg_episode_time', 0):.2f}s")
        print(f"  Peak Memory: {perf_stats.get('peak_memory_mb', 0):.2f} MB")
        print(f"  Episodes/sec: {perf_stats.get('episodes_per_second', 0):.2f}")
        
        print("=" * 60)

    def _run_brain_biopsy(self, episode: int):
        """Run brain biopsy on all agents."""
        import json
        import os
        
        self.logger.logger.info(f"🧠 Running Brain Biopsy for Episode {episode}...")
        
        results_dir = f"results/{self.config.get('name', 'experiment')}_biopsy"
        os.makedirs(results_dir, exist_ok=True)
        
        for agent_id, agent in enumerate(self.coordinator.agents):
            # Inspect population
            biopsy_data = BrainBiopsyTheus.inspect_population(agent.snn_ctx)
            
            # Save to file
            filename = f"{results_dir}/ep{episode}_agent{agent_id}.json"
            with open(filename, 'w') as f:
                json.dump(biopsy_data, f, indent=2)

    def _save_agents(self, episode: int):
        """Save all agent checkpoints."""
        import os
        self.logger.logger.info(f"💾 Saving checkpoints for Episode {episode}...")
        
        checkpoint_dir = f"results/{self.config.get('name', 'experiment')}_checkpoints"
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        for agent_id, agent in enumerate(self.coordinator.agents):
            try:
                # Use library utility
                filepath = save_snn_agent(agent.snn_ctx, agent_id, checkpoint_dir)
                self.logger.logger.info(f"  Saved Agent {agent_id} to {filepath}")
            except Exception as e:
                self.logger.log_error(e, f"Saving Agent {agent_id}")


def main():
    """Run default experiment."""
    config = {
        'name': 'multi_agent_test',
        'num_agents': 5,
        'num_episodes': 10,
        'max_steps': 20,
        'grid_size': 8,
        'num_neurons': 50,
        'social_learning_freq': 3,
        'revolution_threshold': 0.3,
        'revolution_window': 3
    }
    
    experiment = MultiAgentExperiment(config)
    experiment.run()


if __name__ == '__main__':
    main()
