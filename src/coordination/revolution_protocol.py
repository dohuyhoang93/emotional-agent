"""
Revolution Protocol Manager
============================
Manage Revolution Protocol (ancestor updates).

Author: Do Huy Hoang
Date: 2025-12-25
"""
import numpy as np
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.coordination.multi_agent_coordinator import MultiAgentCoordinator


class RevolutionProtocolManager:
    """
    Manage Revolution Protocol (ancestor updates).

    Triggers revolution when population performance exceeds threshold.
    Updates ancestor as weighted average of elite agents.
    
    KEY FEATURE: Cooldown mechanism to prevent infinite triggering.
    """

    def __init__(
        self,
        coordinator: 'MultiAgentCoordinator',
        threshold: float = 0.8,
        window: int = 10,
        elite_ratio: float = 0.1
    ):
        """
        Initialize revolution protocol manager.

        Args:
            coordinator: Multi-agent coordinator
            threshold: Performance threshold to trigger revolution
            window: Number of episodes to average (also cooldown period)
            elite_ratio: Top % of agents for ancestor (default 10%)
        """
        self.coordinator = coordinator
        self.threshold = threshold
        self.window = window
        self.elite_ratio = elite_ratio

        # Revolution history
        self.last_trigger_episode = -1000  # ← COOLDOWN TRACKER
        self.dynamic_baseline = threshold  # Start with initial threshold
        self.revolution_count = 0  # ← FIX: Initialize counter
        self.revolution_history = []  # ← FIX: Initialize history

    def check_and_execute_revolution(self) -> bool:
        """
        Check if revolution should be triggered and execute if needed.

        Criteria:
        - Average performance over window > dynamic_baseline
        - Cooldown period respected (at least window episodes since last trigger)

        Returns:
            True if revolution was triggered
        """
        perf = self.coordinator.population_performance
        current_ep = self.coordinator.episode_count

        if len(perf) < self.window:
            # Auto-initialize baseline if not set correctly
            if len(perf) > 0 and self.dynamic_baseline < 1.0 and np.mean(perf) > 10.0:
                 self.dynamic_baseline = np.mean(perf)
            return False

        # ========================================
        # KEY FIX: COOLDOWN CHECK
        # ========================================
        if (current_ep - self.last_trigger_episode) < self.window:
            return False  # ← PREVENTS RAPID RE-TRIGGERING

        # Check recent performance
        recent_avg = np.mean(perf[-self.window:])

        # Auto-calib baseline
        if self.dynamic_baseline < 1.0 and recent_avg > 10.0:
             self.dynamic_baseline = recent_avg
             return False  # Don't trigger on calibration step

        if recent_avg > self.dynamic_baseline:
            self.last_trigger_episode = current_ep  # ← UPDATE TIMESTAMP
            self._execute_revolution(recent_avg)
            return True

        return False

    def _execute_revolution(self, triggering_performance: float):
        """
        Execute revolution: Update ancestor.

        Steps:
        1. Identify top elite agents
        2. Extract their synapse weights
        3. Compute weighted average
        4. Update ancestor in all agents
        5. Update Baseline
        """
        # Get elite agents
        rankings = self.coordinator.get_agent_rankings()
        num_elite = max(1, int(len(rankings) * self.elite_ratio))
        elite_ids = [r[0] for r in rankings[:num_elite]]

        # Collect weights from elite (as Dicts)
        all_weights_dicts = []
        all_synapse_ids = set()

        for elite_id in elite_ids:
            agent = self.coordinator.agents[elite_id]
            # Use Dict {id: weight}
            weights_dict = {
                s.synapse_id: s.weight
                for s in agent.snn_ctx.domain_ctx.synapses
            }
            all_weights_dicts.append(weights_dict)
            all_synapse_ids.update(weights_dict.keys())

        if not all_weights_dicts:
            return

        # Compute average (ancestor) per Synapse ID
        ancestor_weights = {}
        for syn_id in all_synapse_ids:
            values = []
            for w_dict in all_weights_dicts:
                if syn_id in w_dict:
                    values.append(w_dict[syn_id])

            if values:
                ancestor_weights[syn_id] = float(np.mean(values))

        # Update all agents
        for agent in self.coordinator.agents:
            agent.snn_ctx.domain_ctx.ancestor_weights = ancestor_weights

        # Update coordinator's shared ancestor
        self.coordinator.ancestor_weights = ancestor_weights

        # Update Baseline for NEXT revolution
        self.dynamic_baseline = triggering_performance

        # Record revolution
        self.revolution_count += 1
        self.revolution_history.append({
            'episode': self.coordinator.episode_count,
            'elite_ids': elite_ids,
            'num_weights': len(ancestor_weights),
            'avg_weight': float(np.mean(np.abs(list(ancestor_weights.values())))),
            'new_baseline': self.dynamic_baseline
        })

    def get_revolution_stats(self) -> Dict[str, Any]:
        """Get revolution statistics."""
        if not self.revolution_history:
            return {
                'total_revolutions': 0,
                'last_revolution': None,
                'current_baseline': self.dynamic_baseline
            }

        return {
            'total_revolutions': self.revolution_count,
            'last_revolution': self.revolution_history[-1],
            'current_baseline': self.dynamic_baseline,
            'revolutions_per_100_episodes': (
                self.revolution_count / self.coordinator.episode_count * 100
                if self.coordinator.episode_count > 0 else 0
            )
        }
