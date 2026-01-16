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
        # Execute Dream Workflow YAML
        self.engine.execute_workflow("workflows/agent_dream.yaml")
    
    # _register_all_processes removed (Refactoring Phase 1.3)
    # Reliance on engine.scan_and_register('src/processes')
    
    def reset(self, observation: Dict[str, Any]):
        """
        Reset agent cho episode mới.
        
        Args:
            observation: Initial observation từ environment
        """
        # Flush recorder if active (Handled by process logic? No, reset flushes buffer usually)
        # In POP, buffer is in context. We can clear it or flush it. 
        # Ideally, we should flush manually here if we want to save end-of-episode?
        # Actually, if buffer > 0, we can flush. 
        # Let's clean buffer on reset.
        if self.domain_ctx.recorder_config:
             # Explicitly flush remaining?
             # For simplicity/safety, just clear buffer on reset. 
             # Or we can invoke process? No process invocation here easily without creating new transaction.
             # Just clear buffer to prevent leak across episodes. 
             # Safe Flush logic implies we want to SAVE data.
             # We will skip saving 'tail' of episode for now to avoid complexity, or implement a manual flush util.
             # Decision: Clear buffer to solve memory leak absolutely.
             if self.domain_ctx.heavy_recorder_buffer:
                 self.domain_ctx.heavy_recorder_buffer.clear()
        
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
                neuron.last_fire_time = -1000  # Reset to ensure valid refractory check
            
            # Clear spike queue
            self.snn_ctx.domain_ctx.spike_queue.clear()
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
    
    def step(self, env_adapter: EnvironmentAdapter) -> int:
        """
        Execute one step.
        
        Args:
            env_adapter: Environment adapter
            
        Returns:
            Selected action (0-3)
        """
        # Inject adapter into context for processes to use (v3 Context-based approach)
        with self.engine.edit():
            self.domain_ctx.env_adapter = env_adapter

        # Run workflow (Manual Pipeline for Performance/Safety)
        # Bypassing self.engine.execute_workflow to avoid nested loop/thread issues
        from src.processes.agent_step_pipeline import run_agent_step_pipeline
        run_agent_step_pipeline(self.rl_ctx)
        
        # Record Step (Phase 15 - Legacy)
        # REMOVED: Handled by workflow process 'process_record_snn_step'
        # if self.recorder: ...
        
        # Update metrics
        self.episode_metrics['steps'] += 1
        
        # DEBUG: Trace steps
        # print(f"Agent {self.agent_id} Step {self.episode_metrics['steps']}")
        # if self.episode_metrics['steps'] % 10 == 0:
        #    print(f"Agent {self.agent_id} Step {self.episode_metrics['steps']}")
            
        return self.domain_ctx.last_action
    
    def observe_reward(self, extrinsic_reward: float):
        """
        Receive extrinsic reward from environment and update metrics.
        Called by Coordinator after action execution.
        """
        # Calculate total reward
        intrinsic = self.domain_ctx.intrinsic_reward if hasattr(self.domain_ctx, 'intrinsic_reward') else 0.0
        
        # Apply weighting (Prevent Curiosity Hacking)
        weight = getattr(self.global_ctx, 'intrinsic_reward_weight', 0.1)
        
        total = extrinsic_reward + (intrinsic * weight)
        
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
