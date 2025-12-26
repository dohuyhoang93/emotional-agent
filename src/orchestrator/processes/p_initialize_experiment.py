from theus import process
from src.orchestrator.context import OrchestratorSystemContext
from src.logger import log as system_log, log_error as system_log_error
from src.coordination.multi_agent_coordinator import MultiAgentCoordinator
from src.adapters.environment_adapter import EnvironmentAdapter
from environment import GridWorld as ComplexMazeEnvV2
from src.utils.snn_persistence import save_snn_agent
import os
import json

class ExperimentLogger:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.metrics_file = os.path.join(output_dir, "metrics.json")
        self.episode_data = []
        
    def log_episode(self, episode, metrics):
        entry = {'episode': episode, 'metrics': metrics}
        self.episode_data.append(entry)
        # Append to file (or rewrite)
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.episode_data, f, indent=2)
        except Exception as e:
            traceback.print_exc()
            print(f"Error logging metrics: {e}")

class FSMExperimentRunner:
    """
    Lightweight container for running experiments in FSM.
    Replaces legacy MultiAgentExperiment.
    """
    def __init__(self, config, output_dir):
        # NOTE: config is a DICT (exp_def.parameters)
        self.config = config
        self.output_dir = output_dir
        self.current_episode_count = 0
        
        # 1. Setup Environment
        env_config = config.get('environment_config', {}) if 'environment_config' in config else config.get('environment', {})
        print(f"DEBUG: FSMRunner env_config keys: {list(env_config.keys())}")
        print(f"DEBUG: FSMRunner env_config num_agents: {env_config.get('num_agents')}")
        
        
        # GridWorld expects the PARENT config (containing 'environment_config' key)
        # self.config is the dict { ..., 'environment_config': {...} }
        self.env = ComplexMazeEnvV2(self.config) # GridWorld
        print(f"DEBUG: GridWorld num_agents: {self.env.num_agents}")
        
        self.adapter = EnvironmentAdapter(self.env)
        
        # 2. Setup Contexts for Coordinator
        from src.core.context import GlobalContext
        from src.core.snn_context_theus import SNNGlobalContext
        
        # Retrieve settings
        num_agents = env_config.get('num_agents', 1)
        max_steps = env_config.get('max_steps_per_episode', 100)
        
# HACK: Create GlobalContext from config
        # GlobalContext fields: initial_needs, initial_emotions, etc.
        # config is exp_def.parameters (contains both Agent and SNN params usually mixed)
        global_ctx = GlobalContext()
        for k, v in self.config.items():
            if hasattr(global_ctx, k):
                setattr(global_ctx, k, v)
        
        # Override defaults if needed
        global_ctx.max_steps = max_steps
        # Map some fields if names differ
        if 'needs' in self.config and not global_ctx.initial_needs:
             global_ctx.initial_needs = self.config['needs']
        if 'emotions' in self.config and not global_ctx.initial_emotions:
             global_ctx.initial_emotions = self.config['emotions']
        
        # Create SNN Global Context
        snn_config = self.config.get('snn_config', {})
        # Filter keys to match SNNGlobalContext fields (to avoid TypeError)
        # For now, simplistic try-catch or just pass **snn_config if we trust it.
        # Ideally we use the factory or just defaults.
        # Only pass known args if possible, or expect exact config matches.
        # Let's use defaults + manual update to be safe against random keys.
        snn_global_ctx = SNNGlobalContext()
        for k, v in snn_config.items():
            if hasattr(snn_global_ctx, k):
                setattr(snn_global_ctx, k, v)
        
        # 3. Setup Coordinator
        self.coordinator = MultiAgentCoordinator(num_agents, global_ctx, snn_global_ctx)
        
        # 3. Setup Logger
        self.logger = ExperimentLogger(output_dir)
        
        # 4. Performance Monitor (Mock for now or reuse legacy if portable)
        class PerfMonitor:
            def start_episode(self): pass
            def end_episode(self): pass
        self.perf_monitor = PerfMonitor()
        
        # 5. Revolution (Mock or Implement)
        class RevolutionMock:
            def check_and_execute_revolution(self): return False
        self.revolution = RevolutionMock()
        
        # Agents are already initialized in Coordinator __init__
        # self.coordinator.initialize_agents()
        
    def initialize_run(self, run_idx):
        """Initialize a new run (reset episode count)."""
        self.current_episode_count = 0
        # Additional run setup if needed
        
    def run_episode(self, episode_idx):
        """Run a single episode wrapper."""
        self.perf_monitor.start_episode()
        metrics = self.coordinator.run_episode(self.env, self.adapter)
        self.perf_monitor.end_episode()
        
        self.logger.log_episode(episode_idx, metrics)
        self.current_episode_count += 1
        return metrics

@process(
    inputs=['domain.active_experiment_idx', 'domain.experiments', 'domain.event_bus', 'domain.output_dir', 'log_level'],
    outputs=['domain.experiments'],
    side_effects=['memory.allocate'],
    errors=[]
)
def initialize_active_experiment(ctx: OrchestratorSystemContext):
    """
    Process: Khởi tạo Runner cho thí nghiệm hiện tại.
    """
    domain = ctx.domain_ctx
    bus = domain.event_bus
    
    if domain.active_experiment_idx >= len(domain.experiments):
        if bus: bus.emit("ALL_EXPERIMENTS_DONE")
        return

    exp_def = domain.experiments[domain.active_experiment_idx]
    
    system_log(ctx, "info", f"Initializing Experiment: {exp_def.name}")
    
    # Create Runner
    output_subdir = os.path.join(domain.output_dir, f"{exp_def.name}_checkpoints")
    os.makedirs(output_subdir, exist_ok=True)
    
    runner = FSMExperimentRunner(exp_def.parameters, output_subdir)
    
    # Store runner in ExperimentDefinition
    exp_def.runner = runner
    
    system_log(ctx, "info", f"Experiment {exp_def.name} initialized ready for FSM loop.")
    if bus: bus.emit("INIT_DONE")

