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

from theus.engine import TheusEngine
from src.core.context import SystemContext
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
        rl_ctx: SystemContext,
        engine: TheusEngine,
        audit_recipe: Optional[Any] = None
    ):
        """
        Initialize RL Agent.
        
        Args:
            rl_ctx: Theus SystemContext (Global + Domain)
            engine: Configured TheusEngine
            audit_recipe: Audit recipe (optional)
        """
        self.engine = engine
        self.rl_ctx = rl_ctx
        self.global_ctx = rl_ctx.global_ctx
        self.agent_id = rl_ctx.domain_ctx.agent_id
        
        # SNN Context (Link via Domain)
        # Assuming rl_ctx.domain_ctx.snn_context is initialized by Caller or empty?
        # In current logic, RLAgent inits SNN Context. 
        # Domain Context is now in rl_ctx.domain_ctx
        self.domain_ctx = rl_ctx.domain_ctx
        
        
        # SNN Components
        # Expecting SNN Context to be injected via Domain Context
        self.snn_ctx = self.domain_ctx.snn_context
        if self.snn_ctx is None:
             raise ValueError("RLAgent requires an injected snn_context in domain_ctx")
        
        # Gated Integration Network
        # Gated Integration Network
        # Configuration from GlobalContext (Phase 2)
        model_cfg = getattr(self.global_ctx, 'model_config', {})
        
        obs_dim = model_cfg.get('obs_dim', 5)
        emotion_dim = model_cfg.get('emotion_dim', 16)
        hidden_dim = model_cfg.get('hidden_dim', 64)
        action_dim = model_cfg.get('action_dim', 8)
        gated_lr = model_cfg.get('gated_lr', 0.001)
        
        self.gated_network = GatedIntegrationNetwork(
            obs_dim=obs_dim,
            emotion_dim=emotion_dim,
            hidden_dim=hidden_dim,
            action_dim=action_dim
        )
        self.optimizer = torch.optim.Adam(
            self.gated_network.parameters(),
            lr=gated_lr
        )
        
        # Link state to Domain Context (Safe Mutation)
        with self.engine.edit():
            self.domain_ctx.heavy_gated_network = self.gated_network
            self.domain_ctx.heavy_gated_optimizer = self.optimizer
        
        
        
        # === AUDIT RECIPE LOADING (Activated by User) ===
        # We load specs/snn_audit_recipe.yaml manually here
        from theus.config import AuditRecipe
        import os
        # Loading Audit Recipe (Phase 13)
        # Using self.agent_id since agent_id arg is removed
        if audit_recipe is None:
             # Try load from file based on Agent ID
             try:
                 import json
                 recipe_path = f"audit_recipes/agent_{self.agent_id}.json"
                 if os.path.exists(recipe_path):
                     with open(recipe_path, 'r') as f:
                         recipe_dict = json.load(f)
                     audit_recipe = AuditRecipe(recipe_dict)
                     print(f"✅ RLAgent {self.agent_id}: Loaded Audit Recipe from {recipe_path}")
             except Exception as e:
                 print(f"⚠️ Failed to load Audit Recipe: {e}")

        # Theus Engine (Injected) already assigned self.engine = engine
        
        # Verify Engine is scanned (Optional safety check)
        # engine.scan_and_register(...) is responsibility of the caller
        
        # Register manual aliases (overrides scan if colliding, or adds new aliases)
        # Scan and Register is sufficient
        # self._register_all_processes()
        
        # Metrics
        self.episode_metrics = {
            'total_reward': 0.0,
            'intrinsic_reward_total': 0.0,
            'extrinsic_reward_total': 0.0,
            'steps': 0
        }
        
        # Phase 14: Sleep & Dream
        self.is_sleeping = False
        
        # Recorder (Feature Flag in GlobalContext)
        if getattr(self.global_ctx, 'enable_recorder', False):
             # POP REFACTOR: SNNRecorder class removed. 
             # We configure context for process_record_snn_step
             output_dir = os.path.join("results", "recordings")
             
             with self.engine.edit():
                 self.domain_ctx.recorder_config = {
                    'agent_id': self.agent_id,
                    'output_dir': output_dir,
                    'buffer_size': 1000
                 }
                 # Ensure buffer init (Done by dataclass default, but safe to touch)
                 if self.domain_ctx.heavy_recorder_buffer is None:
                     self.domain_ctx.heavy_recorder_buffer = []
             
             # self.recorder = SNNRecorder(...) # DEPRECATED
             self.recorder = None # Flag for manual calls removal
        else:
             self.recorder = None
             with self.engine.edit():
                 self.domain_ctx.recorder_config = None
    
    # Phase 14: Sleep & Dream
    # ==========================
    def start_sleep(self):
        """Enter sleep mode: Disable sensors."""
        self.is_sleeping = True
    
    def wake_up(self):
        """Exit sleep mode: Re-enable sensors."""
        self.is_sleeping = False
        
    def dream_step(self, time_step):
        """
        Execute one step of dreaming.
        
        Logic:
        1. Inject Dream Stimulus (Noise/Replay) -> spike_queue
        2. Run SNN Cycle (Integrate -> Fire -> STDP)
        3. Decode Dream State (Visualizing the dream)
        4. (Optional) Run Post-Cycle logic (Darwinism, etc.) - maybe skipped for stability.
        """
        # NOTE: Dream processes access domain_ctx.snn_context which is a live Python object.
        # Routing through self.engine.execute() serializes context into Rust Core,
        # which LOSES complex Python refs (snn_context becomes a flat dict).
        # We call process functions directly with self.rl_ctx to preserve live references.
        from src.processes.snn_dream_processes import (
            process_inject_dream_stimulus, apply_dream_reward
        )
        from src.processes.snn_core_theus import process_integrate, process_fire
        from src.processes.snn_advanced_features_theus import (
            process_lateral_inhibition, process_hysteria_dampener
        )
        from src.processes.snn_learning_3factor_theus import process_stdp_3factor
        from src.processes.p_dream_decoder import process_decode_dream
        
        ctx = self.rl_ctx
        try:
            process_inject_dream_stimulus(ctx)
            process_hysteria_dampener(ctx)
            process_integrate(ctx)
            process_lateral_inhibition(ctx)
            process_fire(ctx)
            apply_dream_reward(ctx)
            process_stdp_3factor(ctx)
            process_decode_dream(ctx)
        except Exception as e:
            import logging
            logging.getLogger("Theus").warning(f"Dream step {time_step} failed: {e}")
    
    # _register_all_processes removed (Refactoring Phase 1.3)
    # Reliance on engine.scan_and_register('src/processes')
    
    def reset(self, observation: Dict[str, Any], full_reset: bool = False):
        """
        Reset agent cho episode mới.
        
        Args:
            observation: Initial observation từ environment
            full_reset: Nếu True, reset toàn bộ thời gian và lịch sử (dùng khi bắt đầu Run mới)
        """
        # Flush recorder if active
        if self.domain_ctx.recorder_config:
             if self.domain_ctx.heavy_recorder_buffer:
                 self.domain_ctx.heavy_recorder_buffer.clear()
        
        with self.engine.edit():
            # Reset RL state
            self.domain_ctx.current_observation = observation
            self.domain_ctx.previous_observation = None
            self.domain_ctx.current_step = 0
            self.domain_ctx.last_reward = {'extrinsic': 0.0, 'intrinsic': 0.0}
            self.domain_ctx.last_action = None
            
            # Reset SNN state - CHỈ reset nếu full_reset=True hoặc dữ liệu chưa tồn tại
            for neuron in self.snn_ctx.domain_ctx.neurons:
                neuron.potential = 0.0
                neuron.potential_vector = np.zeros(16)
                if full_reset:
                    neuron.fire_count = 0
                    neuron.last_fire_time = -1000  # Reset tuổi thọ
                
            # NEW SNN POP FIX: Reset heavy tensors
            if hasattr(self.snn_ctx.domain_ctx, 'heavy_tensors') and self.snn_ctx.domain_ctx.heavy_tensors:
                t = self.snn_ctx.domain_ctx.heavy_tensors
                if 'potentials' in t:
                     t['potentials'].fill(0.0)
                if 'potential_vectors' in t:
                     t['potential_vectors'].fill(0.0)
                if full_reset:
                    if 'last_fire_times' in t:
                         t['last_fire_times'].fill(-1000)
                    if 'thresholds' in t:
                         initial_th = getattr(self.global_ctx, 'initial_threshold', 0.05)
                         t['thresholds'].fill(initial_th)
                if 'spike_buffer' in t:
                     t['spike_buffer'].fill(0)
            
            # Clear spike queue
            self.snn_ctx.domain_ctx.spike_queue.clear()
            if full_reset:
                self.snn_ctx.domain_ctx.current_time = 0
            
            # Reset metrics
            self.episode_metrics = {
                'total_reward': 0.0,
                'intrinsic_reward_total': 0.0,
                'extrinsic_reward_total': 0.0,
                'steps': 0,
                'success': False,
                'steps_to_goal': None
            }
            
            # Reset SNN metrics
            if 'accumulated_spikes' in self.snn_ctx.domain_ctx.metrics:
                self.snn_ctx.domain_ctx.metrics['accumulated_spikes'] = 0
            if 'accumulated_ticks' in self.snn_ctx.domain_ctx.metrics:
                self.snn_ctx.domain_ctx.metrics['accumulated_ticks'] = 0
            
            # Reset PID Controller States (State of the controller itself)
            if hasattr(self.snn_ctx.domain_ctx, 'pid_state'):
                for key in self.snn_ctx.domain_ctx.pid_state:
                    self.snn_ctx.domain_ctx.pid_state[key]['error_integral'] = 0.0
                    self.snn_ctx.domain_ctx.pid_state[key]['error_prev'] = 0.0
    
    def step(self, env_adapter: EnvironmentAdapter) -> int:
        """
        Execute one step.
        
        Args:
            env_adapter: Environment adapter
            
        Returns:
            Selected action (0-3)
        """
        # NOTE: Gọi trực tiếp thay vì qua engine.execute_sync.
        # execute_sync dùng asyncio, nhưng method này được gọi từ ThreadPoolExecutor
        # (multi_agent_coordinator.py). asyncio event loop không có trong worker threads
        # → sẽ deadlock hoặc fail. Direct call là cách đúng ở đây.
        with self.engine.edit():
            self.domain_ctx.env_adapter = env_adapter

        from src.processes.agent_step_pipeline import run_agent_step_pipeline
        run_agent_step_pipeline(self.rl_ctx)
        
        # Update metrics
        self.episode_metrics['steps'] += 1
        
        # DEBUG: Trace steps
        # print(f"Agent {self.agent_id} Step {self.episode_metrics['steps']}")
        # if self.episode_metrics['steps'] % 10 == 0:
        #    print(f"Agent {self.agent_id} Step {self.episode_metrics['steps']}")
            
        return self.domain_ctx.last_action
    
    def observe_reward_and_learn(self, extrinsic_reward: float, next_obs: Dict[str, Any]):
        """
        Receive extrinsic reward and next observation, then update SNN/RL models.
        This fixes the 'Double Move' bug by decoupling thinking from execution.
        
        NOTE: Gọi trực tiếp, không qua execute_sync — tránh asyncio deadlock trong thread.
        """
        from src.processes.rl_snn_integration import combine_rewards
        from src.processes.rl_processes import update_q_learning

        # NOTE: previous_observation PHẢI được gán TRƯỚC khi ghi đè current_observation.
        # Nếu không, update_q_learning sẽ thấy previous_observation=None và luôn skip.
        with self.engine.edit():
            self.domain_ctx.previous_observation = self.domain_ctx.current_observation
            self.domain_ctx.current_observation = next_obs
            self.domain_ctx.last_reward = {
                'extrinsic': extrinsic_reward,
                'intrinsic': 0.0,
                'total': extrinsic_reward
            }

        def _apply(delta):
            if not isinstance(delta, dict): return
            for k, v in delta.items():
                if k.startswith('domain_ctx.'): k = k.replace('domain_ctx.', '')
                setattr(self.domain_ctx, k, v)

        _apply(combine_rewards(self.rl_ctx))
        _apply(update_q_learning(self.rl_ctx))
        
        # 2. Accumulate metrics from updated context
        reward_dict = self.domain_ctx.last_reward
        total = reward_dict.get('total', extrinsic_reward)
        intrinsic = reward_dict.get('intrinsic', 0.0)
        
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
                'q_table_size': len(self.domain_ctx.heavy_q_table)
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
