"""
RL Agent with SNN Integration
==============================
Agent class tích hợp SNN emotion processing và RL decision making.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
import torch
from typing import Dict, Any, Optional

from theus import TheusEngine
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.snn_context_theus import (
    create_snn_context_theus,
    SNNGlobalContext,
    SNNSystemContext
)
from src.models.gated_integration import GatedIntegrationNetwork
from src.adapters.environment_adapter import EnvironmentAdapter


class RLAgent:
    """
    RL Agent với SNN emotion processing.
    
    Components:
    - SNN Context: Emotion processing, synaptic learning
    - Gated Integration Network: Fuse observation + emotion
    - Q-learning: Action selection
    - Intrinsic Reward: Curiosity-driven exploration
    
    Architecture:
        Observation → SNN → Emotion Vector ─┐
                                            ├→ Gated Network → Q-values → Action
        Observation ────────────────────────┘
    """
    
    def __init__(
        self,
        agent_id: int,
        global_ctx: GlobalContext,
        snn_global_ctx: SNNGlobalContext,
        audit_recipe: Optional[Any] = None
    ):
        """
        Initialize RL Agent.
        
        Args:
            agent_id: Agent ID
            global_ctx: RL global context
            snn_global_ctx: SNN global context
            audit_recipe: Theus audit recipe (optional)
        """
        self.agent_id = agent_id
        
        # RL Components
        self.global_ctx = global_ctx
        self.domain_ctx = DomainContext(
            N_vector=torch.tensor(global_ctx.initial_needs),
            E_vector=torch.tensor(global_ctx.initial_emotions),
            believed_switch_states={
                slug: False for slug in global_ctx.switch_locations.keys()
            },
            q_table={},
            short_term_memory=[],
            long_term_memory={},
            base_exploration_rate=global_ctx.initial_exploration_rate,
            current_exploration_rate=global_ctx.initial_exploration_rate
        )
        self.rl_ctx = SystemContext(
            global_ctx=global_ctx,
            domain_ctx=self.domain_ctx
        )
        
        # SNN Components
        self.snn_ctx = create_snn_context_theus(
            num_neurons=snn_global_ctx.num_neurons,
            connectivity=snn_global_ctx.connectivity,
            vector_dim=snn_global_ctx.vector_dim,
            seed=snn_global_ctx.seed
        )
        
        # Link SNN to RL context
        self.domain_ctx.snn_context = self.snn_ctx
        
        # Gated Integration Network
        # obs_dim: (x, y, step_count, norm_x, norm_y)
        obs_dim = 5
        emotion_dim = 16  # SNN emotion vector
        hidden_dim = 64
        action_dim = 4  # up, down, left, right
        
        self.gated_network = GatedIntegrationNetwork(
            obs_dim=obs_dim,
            emotion_dim=emotion_dim,
            hidden_dim=hidden_dim,
            action_dim=action_dim
        )
        self.optimizer = torch.optim.Adam(
            self.gated_network.parameters(),
            lr=0.001
        )
        
        # Theus Engine
        self.engine = TheusEngine(
            self.rl_ctx,
            audit_recipe=audit_recipe,
            strict_mode=True
        )
        
        # Auto-discover processes (use absolute path)
        import os
        processes_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'processes'
        )
        self.engine.scan_and_register(processes_dir)
        
        # Metrics
        self.episode_metrics = {
            'total_reward': 0.0,
            'intrinsic_reward_total': 0.0,
            'extrinsic_reward_total': 0.0,
            'steps': 0
        }
    
    def _register_all_processes(self):
        """Register tất cả processes manually."""
        # Import processes
        from src.processes.snn_rl_bridge import (
            encode_state_to_spikes,
            encode_emotion_vector,
            compute_intrinsic_reward_snn,
            modulate_snn_attention
        )
        from src.processes.rl_processes import (
            select_action_gated,
            update_q_learning
        )
        from src.processes.rl_snn_integration import (
            combine_rewards,
            execute_action_with_env
        )
        from src.processes.snn_core_theus import (
            process_integrate,
            process_fire
        )
        from src.processes.snn_learning_theus import (
            process_clustering
        )
        from src.processes.snn_learning_3factor_theus import (
            process_stdp_3factor
        )
        from src.processes.snn_commitment_theus import (
            process_commitment
        )
        from src.processes.snn_homeostasis_theus import (
            process_homeostasis
        )
        
        # Register SNN-RL bridge
        self.engine.register_process('encode_state_to_spikes', encode_state_to_spikes)
        self.engine.register_process('encode_emotion_vector', encode_emotion_vector)
        self.engine.register_process('compute_intrinsic_reward_snn', compute_intrinsic_reward_snn)
        self.engine.register_process('modulate_snn_attention', modulate_snn_attention)
        
        # Register RL processes
        self.engine.register_process('select_action_gated', select_action_gated)
        self.engine.register_process('update_q_learning', update_q_learning)
        
        # Register RL-SNN integration
        self.engine.register_process('combine_rewards', combine_rewards)
        self.engine.register_process('execute_action_with_env', execute_action_with_env)
        
        # Register SNN core
        self.engine.register_process('snn_integrate', process_integrate)
        self.engine.register_process('snn_fire', process_fire)
        self.engine.register_process('snn_clustering', process_clustering)
        self.engine.register_process('snn_stdp_3factor', process_stdp_3factor)
        self.engine.register_process('process_commitment', process_commitment)
        self.engine.register_process('process_homeostasis', process_homeostasis)
    
    def reset(self, observation: Dict[str, Any]):
        """
        Reset agent cho episode mới.
        
        Args:
            observation: Initial observation từ environment
        """
        with self.engine.edit():
            # Reset RL state
            self.domain_ctx.current_observation = observation
            self.domain_ctx.previous_observation = None
            self.domain_ctx.current_step = 0
            self.domain_ctx.last_reward = {'extrinsic': 0.0, 'intrinsic': 0.0}
            self.domain_ctx.last_action = None
            
            # Reset SNN state
            for neuron in self.snn_ctx.domain_ctx.neurons:
                neuron.potential = 0.0
                neuron.potential_vector = np.zeros(16)
                neuron.fire_count = 0
            
            # Clear spike queue
            self.snn_ctx.domain_ctx.spike_queue.clear()
            self.snn_ctx.domain_ctx.current_time = 0
            
            # Reset metrics
            self.episode_metrics = {
                'total_reward': 0.0,
                'intrinsic_reward_total': 0.0,
                'extrinsic_reward_total': 0.0,
                'steps': 0
            }
    
    def step(self, env_adapter: EnvironmentAdapter) -> int:
        """
        Execute one step.
        
        Args:
            env_adapter: Environment adapter
            
        Returns:
            Selected action (0-3)
        """
        # Run workflow
        self.engine.execute_workflow(
            "workflows/agent_main.yaml",
            env_adapter=env_adapter,
            agent_id=self.agent_id
        )
        
        # Update metrics
        self.episode_metrics['steps'] += 1
        self.episode_metrics['total_reward'] += self.domain_ctx.last_reward.get('total', 0.0)
        self.episode_metrics['intrinsic_reward_total'] += self.domain_ctx.intrinsic_reward
        self.episode_metrics['extrinsic_reward_total'] += self.domain_ctx.last_reward.get('extrinsic', 0.0)
        
        return self.domain_ctx.last_action
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.
        
        Returns:
            Dict with RL and SNN metrics
        """
        return {
            'rl': {
                **self.episode_metrics,
                'exploration_rate': self.domain_ctx.current_exploration_rate,
                'q_table_size': len(self.domain_ctx.q_table)
            },
            'snn': {
                'fire_rate': self.snn_ctx.domain_ctx.metrics.get('fire_rate', 0.0),
                'active_synapses': len(self.snn_ctx.domain_ctx.synapses),
                'solid_synapses': self.snn_ctx.domain_ctx.metrics.get('solid_synapses', 0),
                'current_time': self.snn_ctx.domain_ctx.current_time
            }
        }
    
    def train_gated_network(self, batch_size: int = 32):
        """
        Train Gated Integration Network (optional).
        
        NOTE: Hiện tại network học online qua gradient descent.
        Method này cho batch training nếu cần.
        
        Args:
            batch_size: Batch size for training
        """
        # TODO: Implement batch training nếu cần
        pass
