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
from src.utils.snn_recorder import SNNRecorder


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
        
        # Inject into Domain Context for processes
        self.domain_ctx.gated_network = self.gated_network
        self.domain_ctx.gated_optimizer = self.optimizer
        
        
        
        # === AUDIT RECIPE LOADING (Activated by User) ===
        # We load specs/snn_audit_recipe.yaml manually here
        from theus.config import AuditRecipe
        import yaml
        import os
        
        # Ensure strict audit is used if none provided
        if audit_recipe is None:
            recipe_path = "specs/snn_audit_recipe.yaml"
            if os.path.exists(recipe_path):
                try:
                    with open(recipe_path, "r", encoding='utf-8') as f:
                        recipe_dict = yaml.safe_load(f)
                    audit_recipe = AuditRecipe(recipe_dict)
                    print(f"✅ RLAgent {agent_id}: Loaded Audit Recipe from {recipe_path}")
                except Exception as e:
                    print(f"⚠️ Failed to load Audit Recipe: {e}")

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
        
        # Register manual aliases (overrides scan if colliding, or adds new aliases)
        self._register_all_processes()
        
        # Metrics
        self.episode_metrics = {
            'total_reward': 0.0,
            'intrinsic_reward_total': 0.0,
            'extrinsic_reward_total': 0.0,
            'steps': 0
        }
        
        # Recorder (Phase 15: Monitoring)
        self.recorder = None
        if getattr(global_ctx, 'enable_recorder', False):
            import os
            self.recorder = SNNRecorder(
                agent_id=agent_id,
                output_dir=os.path.join("results", "recordings"), # Default dir, orchestrator might override
                buffer_size=1000
            )
    
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
            process_homeostasis,
            process_meta_homeostasis_fixed
        )
        from src.processes.snn_advanced_features_theus import (
            process_hysteria_dampener,
            process_lateral_inhibition,
            process_neural_darwinism
        )
        from src.processes.snn_resync_theus import (
            process_periodic_resync
        )
        # Phase 13: Semantic Dream
        from src.processes.p_dream_decoder import process_decode_dream
        from src.processes.p_dream_validator import process_validate_and_reward
        
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
        self.engine.register_process('process_meta_homeostasis_fixed', process_meta_homeostasis_fixed)
        self.engine.register_process('process_meta_homeostasis_fixed', process_meta_homeostasis_fixed)
        self.engine.register_process('process_resync', process_periodic_resync)
        
        # Register Advanced Features (Phase 9-11)
        self.engine.register_process('process_hysteria_dampener', process_hysteria_dampener)
        self.engine.register_process('process_lateral_inhibition', process_lateral_inhibition)
        self.engine.register_process('process_neural_darwinism', process_neural_darwinism)
        
        # Register Semester Dream (Phase 13)
        self.engine.register_process('process_decode_dream', process_decode_dream)
        self.engine.register_process('process_validate_and_reward', process_validate_and_reward)
    
    def reset(self, observation: Dict[str, Any]):
        """
        Reset agent cho episode mới.
        
        Args:
            observation: Initial observation từ environment
        """
        # Flush recorder if active from previous episode
        if self.recorder:
            self.recorder.flush()
        
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
        
        # Record Step (Phase 15)
        if self.recorder:
            # We record running metrics
            # ep_metrics has 'steps' which is count
            current_step = self.episode_metrics['steps']
            # We assume episode index is handled externally or we pass it? 
            # Actually recorder needs Ep Index. 
            # We don't have Ep Index in RLAgent state easily (it's in Runner).
            # But we can assume sequential or pass it in reset?
            # For now passing 0 or adding episode_count to DomainContext.
            # Let's use 0 for now as placeholder, or self.snn_ctx.domain_ctx.cycle_count
            
            # Better: context likely has it or we just use global timestamp
            self.recorder.record_step(self.snn_ctx, 0, current_step)
        
        # Update metrics
        self.episode_metrics['steps'] += 1
        return self.domain_ctx.last_action
    
    def observe_reward(self, extrinsic_reward: float):
        """
        Receive extrinsic reward from environment and update metrics.
        Called by Coordinator after action execution.
        """
        # Calculate total reward
        intrinsic = self.domain_ctx.intrinsic_reward if hasattr(self.domain_ctx, 'intrinsic_reward') else 0.0
        total = extrinsic_reward + intrinsic
        
        # Update context within transaction
        with self.engine.edit():
            self.domain_ctx.last_reward = {
                'extrinsic': extrinsic_reward,
                'intrinsic': intrinsic,
                'total': total
            }
        
        # Accumulate metrics (Local field, not guarded? Wait, episode_metrics is dict on self)
        # self.episode_metrics is NOT a Context field. It is instance attr. Safe to write?
        # Yes, LockViolationError was on 'last_reward' which is domain_ctx.
        self.episode_metrics['total_reward'] += total
        self.episode_metrics['intrinsic_reward_total'] += intrinsic
        self.episode_metrics['extrinsic_reward_total'] += extrinsic_reward
    
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
