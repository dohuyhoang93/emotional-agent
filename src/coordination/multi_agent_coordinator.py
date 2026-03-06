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
from theus import TheusEngine
import os
import torch
import gc # Memory management
from src.core.context import GlobalContext, DomainContext, SystemContext
from src.core.snn_context_theus import SNNGlobalContext, create_snn_context_theus
from src.adapters.environment_adapter import EnvironmentAdapter
from src.coordination.revolution_protocol import RevolutionProtocolManager
from theus.config import ConfigFactory
from src.utils.shm_tensor_store import ShmTensorStore


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
        
        # NOTE: Shared HeavyZoneAllocator cho tất cả agents.
        # Cho phép zero-copy access khi social learning / revolution protocol.
        self._shm_allocator = None
        try:
            from theus.context import HeavyZoneAllocator
            self._shm_allocator = HeavyZoneAllocator()
            print("[Coordinator] SHM Allocator initialized.")
        except Exception as e:
            print(f"[Coordinator] SHM Allocator unavailable, using plain dict: {e}")
        
        # Create agents
        self.agents: List[RLAgent] = []
        processes_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'processes'
        )
        
        for i in range(num_agents):
            # 1. Create Domain Context
            # Default values (similar to legacy RLAgent init)
            domain_ctx = DomainContext(
                agent_id=i,
                position=global_ctx.start_positions[i] if hasattr(global_ctx, 'start_positions') and i < len(global_ctx.start_positions) else [0,0],
                has_key=False,
                is_at_goal=False,
                last_action=-1,
                emotion_state=np.zeros(16, dtype=np.float32),
                N_vector=torch.tensor(global_ctx.initial_needs) if hasattr(global_ctx, 'initial_needs') else torch.zeros(2),
                heavy_E_vector=torch.tensor(global_ctx.initial_emotions) if hasattr(global_ctx, 'initial_emotions') else torch.zeros(16),
                
                # Beliefs etc (defaults in dataclass are empty usually, but let's be explicit if needed)
                believed_switch_states={slug: False for slug in getattr(global_ctx, 'switch_locations', {}).keys()},
                
                # ML params
                base_exploration_rate=getattr(global_ctx, 'initial_exploration_rate', 1.0),
                current_exploration_rate=getattr(global_ctx, 'initial_exploration_rate', 1.0)
            )
            
            # 2. SNN Context
            snn_ctx = create_snn_context_theus(
                num_neurons=snn_global_ctx.num_neurons,
                connectivity=snn_global_ctx.connectivity,
                vector_dim=snn_global_ctx.vector_dim,
                seed=snn_global_ctx.seed + i,
                initial_threshold=snn_global_ctx.initial_threshold,
                tau_decay=snn_global_ctx.tau_decay,
                threshold_min=snn_global_ctx.threshold_min
            )
            # NOTE: Inject ShmTensorStore vao SNN context.
            # Dict-like interface, backing bằng SharedMemory.
            snn_ctx.domain_ctx.heavy_tensors = ShmTensorStore(
                allocator=self._shm_allocator,
                prefix=f"agent_{i}"
            )
            domain_ctx.snn_context = snn_ctx
            
            # 3. System Context
            # Unwrap proxy for multi-engine architectures
            real_global_ctx = getattr(global_ctx, "_inner", global_ctx)
            system_ctx = SystemContext(
                global_ctx=real_global_ctx,
                domain_ctx=domain_ctx
            )
            
            # 4. Engine
            # Load Full Audit Recipe
            audit_recipe = None
            if os.path.exists("specs/multi_agent_audit.yaml"):
                 try:
                     audit_recipe = ConfigFactory.load_recipe("specs/multi_agent_audit.yaml")
                 except Exception as e:
                     print(f"Failed to load Audit Recipe: {e}")
            
            engine = TheusEngine(
                system_ctx,
                audit_recipe=audit_recipe,
                strict_guards=True
            )
            engine.scan_and_register(processes_dir)
            
            # 5. Agent
            agent = RLAgent(
                rl_ctx=system_ctx,
                engine=engine
            )
            self.agents.append(agent)
        
        # Population-level state
        self.population_performance: List[float] = []
        self.episode_count = 0
        
        self.ancestor_weights: np.ndarray = None # Deprecated, use snn_global_ctx.domain_ctx.ancestor_weights
        
        # Revolution Protocol Manager (with cooldown)
        self.revolution = RevolutionProtocolManager(
            coordinator=self,
            threshold=getattr(global_ctx, 'revolution_threshold', 0.6),
            window=getattr(global_ctx, 'revolution_window', 10),
            elite_ratio=getattr(global_ctx, 'top_elite_percent', 0.1)
        )

    
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
            # Reset SNN Metrics Accumulators
            if hasattr(agent, 'snn_ctx') and agent.snn_ctx:
                 agent.snn_ctx.domain_ctx.metrics['accumulated_spikes'] = 0
                 agent.snn_ctx.domain_ctx.metrics['accumulated_ticks'] = 0
        
        # Run episode
        step_count = 0
        consecutive_errors = 0 # Circuit Breaker
        max_steps = self.global_ctx.max_steps
        max_steps = self.global_ctx.max_steps
        
        while step_count < max_steps:
            # New step (clear broadcast events)
            env.new_step()
            
            # Each agent takes a step
            # if step_count % 10 == 0:
            #     print(f"DEBUG: Heartbeat Step {step_count}/{max_steps}")
            
            for i, agent in enumerate(self.agents):
                try:
                    action = agent.step(env_adapter)
                    
                    # Execute action in environment (THE ONLY MOVE)
                    reward = env.perform_action(i, self._action_to_string(action))
                    
                    # Get next observation after move
                    next_obs = env.get_observation(i)
                    
                    # Feed reward and observation back to agent for Learning
                    agent.observe_reward_and_learn(reward, next_obs)

                    # DEBUG PROBE: Theo dõi sensor 12-15 (Re-enabled by user request)
                    if i == 0:
                        s = env.get_sensor_vector(0)
                        bump_msg = f"BUMP({env.last_bump_types.get(0)})" if env.last_bump_types.get(0) else "Sensing"
                        print(f"🔍 [INC-003 PROBE] Agent 0 Step {step_count} | {bump_msg} | Ch12={s[12]} Ch13={s[13]} Ch14={s[14]} Ch15={s[15]:.3f}", flush=True)
                    elif env.last_bump_types.get(i) == 'dynamic':
                        s = env.get_sensor_vector(i)
                        print(f"🔥 [INC-003 GATE-HIT] Agent {i} HIT DYNAMIC GATE at step {step_count} | Ch13={s[13]}", flush=True)
                    
                    # NEW: Check Goal Achievement explicitly
                    if tuple(env.agent_positions[i]) == env.goal_pos:
                        if not agent.episode_metrics.get('success', False):
                             print(f"\n🏆 SUCCESS: Agent {i} Reached Goal at Step {step_count}!")
                             agent.episode_metrics['success'] = True
                             agent.episode_metrics['steps_to_goal'] = step_count
                    
                except Exception as e:
                    # RUST CORE TRAP: Theus catches KeyboardInterrupt and wraps it in ContractViolationError
                    if "KeyboardInterrupt" in str(e):
                        print("\n🛑 MASTER INTERRUPT: Received Ctrl+C (Caught by Theus). Terminating...")
                        import sys
                        sys.exit(0)

                    import traceback
                    traceback.print_exc()
                    print(f"Agent {i} error: {e}")
                    consecutive_errors += 1
                    if consecutive_errors > 5:
                        print("🚨 CIRCUIT BREAKER TRIPPED: Too many consecutive errors. Aborting Episode.")
                        # FIX INC-001: Trả về dict chuẩn thay vì float('-inf') để tránh crash TypeError
                        return {'error': 'circuit_breaker', 'avg_reward': float('-inf')}
                    continue
                
                # Reset circuit breaker on success
                consecutive_errors = 0
            
            # Increment step
            env.current_step += 1
            step_count += 1
            
            # Check Global Done
            if env.is_done():
                break
        
        # Collect population metrics
        self._collect_population_metrics()
        self.episode_count += 1
        
        # NOTE: Epsilon decay đã chuyển sang orchestrator_flux.yaml (process: decay_exploration_all_agents)
        # Tuân thủ POP - logic trong process, không inline vào coordinator
        
        # Explicit GC
        gc.collect()
        
        return self.get_episode_metrics()

    def _collect_population_metrics(self):
        """Collect metrics from all agents."""
        total_reward = sum(
            agent.episode_metrics['total_reward']
            for agent in self.agents
        )
        avg_reward = total_reward / self.num_agents
        
        # New: Collect success count
        success_count = sum(
            1 for agent in self.agents if agent.episode_metrics.get('success', False)
        )
        success_rate = success_count / self.num_agents
        
        # Store tuple or dict in history?
        # Current code assumes float list. Let's make it robust or separate list.
        # To avoid breaking existing code, assume population_performance is avg_reward.
        # We'll add a new list for success_rates if needed, or just return it in get_episode_metrics.
        
        # Sync to SNN Global Context (Source of Truth for Revolution Protocol)
        # Note: We append only if the process hasn't already (to avoid duplicates if process runs in loop)
        # Actually, let the Coordinator be the one to push the metric.
        if self.agents:
             # Use Agent 0 as the "Leader" / Storage for Population State
             # This allows the Revolution Process (running on Agent 0 context) to see history
             leader_ctx = self.agents[0].snn_ctx.domain_ctx
             if not hasattr(leader_ctx, 'population_performance'):
                 leader_ctx.population_performance = []
             leader_ctx.population_performance.append(avg_reward)
             # === MEMORY LEAK FIX: Limit history size ===
             MAX_HISTORY = 200  # Keep last 200 episodes (enough for Revolution Protocol)
             if len(leader_ctx.population_performance) > MAX_HISTORY:
                 leader_ctx.population_performance = leader_ctx.population_performance[-MAX_HISTORY:]
        
        self.population_performance.append(avg_reward)
        # === MEMORY LEAK FIX: Limit coordinator's history too ===
        if len(self.population_performance) > 200:
            self.population_performance = self.population_performance[-200:]
        
        self.last_success_rate = success_rate # Store for immediate retrieval

    def get_episode_metrics(self) -> Dict[str, Any]:
        """Get metrics for last episode."""
        if not self.population_performance:
            return {}
        
        # Calculate success details
        successes = [agent.episode_metrics.get('success', False) for agent in self.agents]
        success_rate = sum(successes) / len(successes) if successes else 0.0
        
        return {
            'episode': self.episode_count,
            'avg_reward': self.population_performance[-1],
            'success_rate': success_rate,
            'agent_rewards': [
                agent.episode_metrics['total_reward']
                for agent in self.agents
            ],
            'agent_success': successes
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
    def _action_to_string(self, action_id: int) -> str:
        """Helper to convert discrete action ID to string direction."""
        mapping = {
            0: 'up',
            1: 'down', 
            2: 'left',
            3: 'right'
        }
        return mapping.get(action_id, 'stay')

    def cleanup(self):
        """Release shared memory resources."""
        if self._shm_allocator is not None:
            try:
                self._shm_allocator.cleanup()
            except Exception:
                pass

    def __del__(self):
        self.cleanup()
