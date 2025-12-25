"""
Multi-Agent Coordinator
========================
Coordinator cho multi-agent system với SNN-RL integration.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from typing import List, Dict, Any
from src.agents.rl_agent import RLAgent
from src.core.context import GlobalContext
from src.core.snn_context_theus import SNNGlobalContext
from src.adapters.environment_adapter import EnvironmentAdapter


class MultiAgentCoordinator:
    """
    Coordinator cho multi-agent system.
    
    Responsibilities:
    - Agent lifecycle management
    - Episode coordination
    - Population-level metrics
    - Ancestor management (for Revolution Protocol)
    """
    
    def __init__(
        self,
        num_agents: int,
        global_ctx: GlobalContext,
        snn_global_ctx: SNNGlobalContext
    ):
        """
        Initialize coordinator.
        
        Args:
            num_agents: Number of agents
            global_ctx: RL global context
            snn_global_ctx: SNN global context
        """
        self.num_agents = num_agents
        self.global_ctx = global_ctx
        self.snn_global_ctx = snn_global_ctx
        
        # Create agents
        self.agents: List[RLAgent] = []
        for i in range(num_agents):
            agent = RLAgent(
                agent_id=i,
                global_ctx=global_ctx,
                snn_global_ctx=snn_global_ctx
            )
            self.agents.append(agent)
        
        # Population-level state
        self.population_performance: List[float] = []
        self.episode_count = 0
        
        # Shared context for Revolution Protocol
        self.ancestor_weights: np.ndarray = None
    
    def run_episode(self, env, env_adapter: EnvironmentAdapter):
        """
        Run one episode for all agents.
        
        Args:
            env: GridWorld environment
            env_adapter: Environment adapter
            
        Returns:
            Episode metrics
        """
        # Reset environment
        obs_dict = env.reset()
        
        # Reset all agents
        for i, agent in enumerate(self.agents):
            agent.reset(obs_dict[i])
        
        # Run episode
        step_count = 0
        max_steps = self.global_ctx.max_steps
        
        while step_count < max_steps:
            # New step (clear broadcast events)
            env.new_step()
            
            # Each agent takes a step
            for i, agent in enumerate(self.agents):
                try:
                    action = agent.step(env_adapter)
                    
                    # Execute action in environment
                    # NOTE: This is simplified - actual implementation
                    # would handle multi-agent actions properly
                    reward = env.perform_action(i, self._action_to_string(action))
                    
                except Exception as e:
                    print(f"Agent {i} error: {e}")
                    continue
            
            # Increment step
            env.current_step += 1
            step_count += 1
            
            # Check if any agent reached goal
            if env.is_done():
                break
        
        # Collect population metrics
        self._collect_population_metrics()
        self.episode_count += 1
        
        return self.get_episode_metrics()
    
    def _action_to_string(self, action: int) -> str:
        """Convert action index to string."""
        actions = ['up', 'down', 'left', 'right']
        return actions[action] if 0 <= action < 4 else 'up'
    
    def _collect_population_metrics(self):
        """Collect metrics from all agents."""
        total_reward = sum(
            agent.episode_metrics['total_reward']
            for agent in self.agents
        )
        avg_reward = total_reward / self.num_agents
        
        self.population_performance.append(avg_reward)
    
    def get_episode_metrics(self) -> Dict[str, Any]:
        """Get metrics for last episode."""
        if not self.population_performance:
            return {}
        
        return {
            'episode': self.episode_count,
            'avg_reward': self.population_performance[-1],
            'agent_rewards': [
                agent.episode_metrics['total_reward']
                for agent in self.agents
            ]
        }
    
    def get_population_metrics(self) -> Dict[str, Any]:
        """Get population-level metrics."""
        if not self.population_performance:
            return {
                'num_agents': self.num_agents,
                'episodes': 0,
                'avg_reward': 0.0,
                'best_reward': 0.0
            }
        
        return {
            'num_agents': self.num_agents,
            'episodes': self.episode_count,
            'avg_reward': np.mean(self.population_performance[-10:]),
            'best_reward': max(self.population_performance),
            'worst_reward': min(self.population_performance),
            'std_reward': np.std(self.population_performance[-10:])
        }
    
    def get_agent_rankings(self) -> List[tuple]:
        """
        Get agent rankings by performance.
        
        Returns:
            List of (agent_id, total_reward) sorted by reward
        """
        rankings = [
            (i, agent.episode_metrics['total_reward'])
            for i, agent in enumerate(self.agents)
        ]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
