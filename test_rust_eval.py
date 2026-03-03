from theus_core import WorkflowEngine

yaml_content = """
name: test_eval
steps:
  - flux: if
    condition: "domain['sig_experiment_active_idx'] < domain['sig_total_experiments']"
    then:
      - process: yes
    else:
      - process: no
"""

wf_engine = WorkflowEngine(yaml_content, 10, True)

ctx = {
    "domain": {
        "sig_experiment_active_idx": 0, 
        "sig_total_experiments": 1
    }
}

def _sync_wrapper(name, **kwargs):
    print(f"EXECUTED PROCESS: {name}")

wf_engine.execute(ctx, _sync_wrapper)
