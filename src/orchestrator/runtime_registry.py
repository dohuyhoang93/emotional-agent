
# Global Runtime Registry for Non-Serializable Objects
# This serves as a "Heavy Zone" alternative for complex runtime objects 
# that cannot be passed through Theus V3 serialization boundaries or 
# require shared mutable access across process boundaries in the same interpreter.

# Store ExperimentRunners by Experiment Name
experiment_runners = {}

def register_runner(name, runner):
    experiment_runners[name] = runner

def get_runner(name):
    return experiment_runners.get(name)

def clear_runner(name):
    if name in experiment_runners:
        del experiment_runners[name]
