"""
Social Learning Manager
========================
Manage social learning (viral synapse transfer) between agents.

Author: Do Huy Hoang
Date: 2025-12-25
"""
import copy
import numpy as np
from typing import List, Dict, Any
from src.coordination.multi_agent_coordinator import MultiAgentCoordinator


class SocialLearningManager:
    """
    Manage social learning (viral synapse transfer).
    
    Uses existing SNN processes:
    - process_extract_top_synapses
    - process_inject_viral_with_quarantine
    - process_quarantine_validation
    """
    
    def __init__(
        self,
        coordinator: MultiAgentCoordinator,
        elite_ratio: float = 0.2,
        learner_ratio: float = 0.5,
        synapses_per_transfer: int = 10
    ):
        """
        Initialize social learning manager.
        
        Args:
            coordinator: Multi-agent coordinator
            elite_ratio: Top % of agents to extract from (default 20%)
            learner_ratio: Bottom % to inject into (default 50%)
            synapses_per_transfer: Number of synapses to transfer
        """
        self.coordinator = coordinator
        self.elite_ratio = elite_ratio
        self.learner_ratio = learner_ratio
        self.synapses_per_transfer = synapses_per_transfer
        
        # Transfer history
        self.transfer_history: List[Dict[str, Any]] = []
    
    def perform_social_learning(self):
        """
        Transfer synapses from top performers to others.
        
        Steps:
        1. Identify elite agents (top 20%)
        2. Extract their top synapses
        3. Inject into learner agents (bottom 50%)
        4. Track transfer history
        """
        # Get agent rankings
        rankings = self.coordinator.get_agent_rankings()
        
        if len(rankings) < 2:
            return  # Need at least 2 agents
        
        # Identify elite and learners
        num_elite = max(1, int(len(rankings) * self.elite_ratio))
        num_learners = max(1, int(len(rankings) * self.learner_ratio))
        
        elite_ids = [r[0] for r in rankings[:num_elite]]
        learner_ids = [r[0] for r in rankings[-num_learners:]]
        
        # Extract synapses from elite
        elite_synapses = []
        for elite_id in elite_ids:
            agent = self.coordinator.agents[elite_id]
            synapses = self._extract_top_synapses(
                agent,
                k=self.synapses_per_transfer
            )
            elite_synapses.extend(synapses)
        
        # Inject into learners
        for learner_id in learner_ids:
            agent = self.coordinator.agents[learner_id]
            injected_count = self._inject_synapses(agent, elite_synapses)
            
            # Track transfer
            self.transfer_history.append({
                'episode': self.coordinator.episode_count,
                'from': elite_ids,
                'to': learner_id,
                'count': injected_count
            })
    
    def _extract_top_synapses(self, agent, k: int = 10):
        """
        Extract top k synapses from agent.
        
        Args:
            agent: RLAgent instance
            k: Number of synapses to extract
            
        Returns:
            List of top synapses
        """
        synapses = agent.snn_ctx.domain_ctx.synapses
        
        if not synapses:
            return []
        
        # Sort by absolute weight
        sorted_synapses = sorted(
            synapses,
            key=lambda s: abs(s.weight),
            reverse=True
        )
        
        # Return top k
        return sorted_synapses[:k]
    
    def _inject_synapses(self, agent, synapses: List) -> int:
        """
        Inject synapses into agent's network.
        
        NOTE: In full implementation, would use quarantine.
        For now, direct injection.
        
        Args:
            agent: RLAgent instance
            synapses: List of synapses to inject
            
        Returns:
            Number of synapses injected
        """
        if not synapses:
            return 0
        
        injected_count = 0
        
        for synapse in synapses:
            # Clone synapse
            new_synapse = copy.deepcopy(synapse)
            
            # Reset quarantine fields (if using quarantine)
            if hasattr(new_synapse, 'quarantine_time'):
                new_synapse.quarantine_time = 0
            if hasattr(new_synapse, 'validation_score'):
                new_synapse.validation_score = 0.0
            
            # Add to agent's network
            agent.snn_ctx.domain_ctx.synapses.append(new_synapse)
            injected_count += 1
        
        return injected_count
    
    def get_transfer_stats(self) -> Dict[str, Any]:
        """Get transfer statistics."""
        if not self.transfer_history:
            return {
                'total_transfers': 0,
                'total_synapses': 0,
                'avg_synapses_per_transfer': 0.0
            }
        
        total_synapses = sum(t['count'] for t in self.transfer_history)
        
        return {
            'total_transfers': len(self.transfer_history),
            'total_synapses': total_synapses,
            'avg_synapses_per_transfer': total_synapses / len(self.transfer_history),
            'last_transfer': self.transfer_history[-1]
        }
