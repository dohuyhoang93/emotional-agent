from theus.contracts import process
from theus.structures import StateUpdate
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log as system_log
from src.utils.logger import ExperimentLogger 
from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld as ComplexMazeEnvV2

import os
import json
import traceback

class FSMExperimentRunner:
    """
    Lightweight container for running experiments in FSM.
    Replaces legacy MultiAgentExperiment.
    """
    def __init__(self, config, output_dir):
        # NOTE: config is a DICT (exp_def.parameters)
        def _unwrap(val):
            if hasattr(val, "to_dict"):
                try: return val.to_dict()
                except Exception: pass
            if isinstance(val, dict): return {k: _unwrap(v) for k, v in val.items()}
            if isinstance(val, list): return [_unwrap(v) for v in val]
            return val
            
        self.config = _unwrap(config)
        self.output_dir = output_dir
        self.current_episode_count = 0
        
        # 1. Setup Environment
        env_config = self.config.get('environment_config', {}) if 'environment_config' in self.config else self.config.get('environment', {})
        self.env = ComplexMazeEnvV2(self.config) # GridWorld
        self.adapter = EnvironmentAdapter(self.env)
        
        # 2. Setup Contexts for Coordinator
        from src.core.context import GlobalContext
        from src.core.snn_context_theus import SNNGlobalContext
        
        num_agents = env_config.get('num_agents', self.config.get('num_agents', 1))
        max_steps = env_config.get('max_steps_per_episode', self.config.get('max_steps_per_episode', 100))
        
        # print(f"DEBUG INIT: num_agents={num_agents}, max_steps={max_steps}", flush=True)
        
        # HACK: Create GlobalContext from config
        global_ctx = GlobalContext()
        for k, v in self.config.items():
            if hasattr(global_ctx, k):
                setattr(global_ctx, k, v)
        
        global_ctx.max_steps = max_steps
        if 'needs' in self.config and not global_ctx.initial_needs:
             global_ctx.initial_needs = self.config['needs']
        if 'emotions' in self.config and not global_ctx.initial_emotions:
             global_ctx.initial_emotions = self.config['emotions']
             
        if 'model_config' in self.config:
            global_ctx.model_config = self.config['model_config']
        
        # Create SNN Global Context
        snn_config = self.config.get('snn_config', {})
        snn_global_ctx = SNNGlobalContext()
        for k, v in snn_config.items():
            if hasattr(snn_global_ctx, k):
                setattr(snn_global_ctx, k, v)
        
        # 3. Setup Coordinator
        self.coordinator = MultiAgentCoordinator(num_agents, global_ctx, snn_global_ctx)
        
        # 3. Setup Logger
        exp_name = os.path.basename(output_dir).replace("_checkpoints", "")
        self.logger = ExperimentLogger(exp_name, output_dir)
        
        # 4. Performance Monitor
        class PerfMonitor:
            def start_episode(self): pass
            def end_episode(self): pass
        self.perf_monitor = PerfMonitor()
        
        # 5. Revolution Config Injection
        if 'revolution_threshold' in config:
            snn_global_ctx.revolution_threshold = config['revolution_threshold']
        if 'revolution_window' in config:
            snn_global_ctx.revolution_window = config['revolution_window']
        if 'revolution_elite_ratio' in config:
            snn_global_ctx.top_elite_percent = config['revolution_elite_ratio']
        
        # 6. Auto-Resume from Checkpoint
        checkpoint_path = self.config.get('checkpoint_path')
        self.start_episode = self.config.get('start_episode', 0)
        
        if checkpoint_path and os.path.exists(checkpoint_path):
            try:
                from src.tools.brain_biopsy_theus import load_all_agents
                system_log(None, "info", f"🔄 Resuming from checkpoint: {checkpoint_path}")
                
                snn_contexts = [agent.snn_ctx for agent in self.coordinator.agents]
                loaded_contexts = load_all_agents(checkpoint_path, snn_contexts)
                
                for i, agent in enumerate(self.coordinator.agents):
                    agent.snn_ctx = loaded_contexts[i]
                
                system_log(None, "info", f"✅ Checkpoint loaded. Resuming from episode {self.start_episode}")
            except Exception as e:
                system_log(None, "error", f"❌ Failed to load checkpoint: {e}")
                traceback.print_exc()
                self.start_episode = 0
        
        
    def initialize_run(self, run_idx):
        """Initialize a new run (reset episode count)."""
        self.current_episode_count = 0
        
    def run_episode(self, episode_idx):
        """Run a single episode wrapper."""
        self.perf_monitor.start_episode()
        metrics = self.coordinator.run_episode(self.env, self.adapter)
        self.perf_monitor.end_episode()
        
        self.logger.log_episode(episode_idx, metrics)
        self.current_episode_count += 1
        return metrics

@process(
    inputs=['domain_ctx', 'domain', 'domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'domain.output_dir', 'log_level'],
    outputs=['domain.sig_episode_counter', 'domain.sig_max_episodes', 'domain.active_experiment_episode_idx', 'domain.sig_start_episode'],
    side_effects=['memory.allocate'],
    errors=[]
)
def initialize_active_experiment(ctx: OrchestratorSystemContext):
    """
    Process: Initialize the active experiment (FSM Runner).
    Resets Signal Counters for the Episode Loop.
    """
    domain = ctx.domain
    bus = getattr(domain, 'event_bus', None)
    
    active_idx = getattr(domain, 'active_experiment_idx', 0)
    experiments = getattr(domain, 'experiments', [])
    
    import logging
    log_tmp = logging.getLogger("Theus")
    log_tmp.info(f"DEBUG INIT: active_idx={active_idx}, len(experiments)={len(experiments)}")
    
    if active_idx >= len(experiments):
        if bus: bus.emit("ALL_EXPERIMENTS_DONE")
        return 0, 0, 0

    exp_def = experiments[active_idx]
    exp_name = getattr(exp_def, 'name', 'unknown') if not isinstance(exp_def, dict) else exp_def.get('name', 'unknown')
    
    # Create Output Directory
    import os
    output_dir = getattr(domain, 'output_dir', 'results')
    
    with open("DEBUG_EXP.txt", "w") as f:
        f.write(f"exp_name: {repr(exp_name)} (type: {type(exp_name)})\n")
        f.write(f"output_dir: {repr(output_dir)} (type: {type(output_dir)})\n")
        f.write(f"isinstance(exp_def, dict): {isinstance(exp_def, dict)}\n")
        f.write(f"exp_def via type: {type(exp_def)}\n")
        if hasattr(exp_def, 'name'):
            f.write(f"exp_def.name: {repr(getattr(exp_def, 'name'))}\n")
    
    output_subdir = os.path.join(output_dir, exp_name)
        
    os.makedirs(output_subdir, exist_ok=True)
    
    parameters = getattr(exp_def, 'parameters', {}) if not isinstance(exp_def, dict) else exp_def.get('parameters', {})
    
    runner = FSMExperimentRunner(parameters, output_subdir)
    
    # V3 MIGRATION: Use Global Runtime Registry
    from src.orchestrator.runtime_registry import register_runner
    register_runner(exp_name, runner)
    
    system_log(ctx, "info", f"Experiment {exp_name} initialized ready for FSM loop.")
    if bus: bus.emit("INIT_DONE")
    
    # Reset Signals for Episode Loop
    episodes_per_run = getattr(exp_def, 'episodes_per_run', 100) if not isinstance(exp_def, dict) else exp_def.get('episodes_per_run', 100)
    
    # Return StateUpdate Delta
    return {
        'domain.sig_episode_counter': 0,
        'domain.sig_max_episodes': episodes_per_run,
        'domain.active_experiment_episode_idx': 0,
        'domain.sig_start_episode': getattr(runner, 'start_episode', 0)
    }
