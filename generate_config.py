import json

def expand_line(line_def):
    coords = []
    start = line_def['start']
    end = line_def['end']
    y1, x1 = start
    y2, x2 = end

    if y1 == y2: # Horizontal
        for x in range(min(x1, x2), max(x1, x2) + 1):
            coords.append([y1, x])
    elif x1 == x2: # Vertical
        for y in range(min(y1, y2), max(y1, y2) + 1):
            coords.append([y, x1])
    return coords

def generate_config():
    base_parameters = {
        "initial_exploration": 1.0,
        "min_exploration": 0.05,
        "exploration_decay": 0.9995
    }
    
    # "Balanced Maze" v2 design
    base_env_config = {
        "grid_size": 25,
        "start_pos": [0, 0],
        "goal_pos": [24, 24],
        "max_steps_per_episode": 3000,
        "walls": [
            # --- Static Wall Segments (broken to avoid cages) ---
            # C-shape near start
            {"type": "line", "start": [0, 5], "end": [8, 5]},
            {"type": "line", "start": [8, 5], "end": [8, 10]},
            # U-shape in middle-left
            {"type": "line", "start": [12, 0], "end": [12, 8]},
            {"type": "line", "start": [12, 8], "end": [20, 8]},
            {"type": "line", "start": [20, 0], "end": [20, 8]},
            # Barrier in middle-right
            {"type": "line", "start": [5, 15], "end": [15, 15]},
            # L-shape near goal (BROKEN UP)
            {"type": "line", "start": [22, 18], "end": [24, 18]}, # Short horizontal segment
            {"type": "line", "start": [18, 22], "end": [18, 24]}, # Short vertical segment
        ],
        "logical_switches": [
            { "pos": [1, 1], "id": "A" },      # Inside starting area
            { "pos": [10, 2], "id": "B" },     # Requires navigating out of start
            { "pos": [15, 12], "id": "C" },    # Mid-maze
            { "pos": [16, 20], "id": "D" },    # Near the new dynamic gate
            { "pos": [22, 22], "id": "E" }     # Near goal
        ],
        "dynamic_walls": [
            # Gate 1: Blocks exit from starting area
            {"id": "gate_A", "pos": [{"type": "line", "start": [9, 0], "end": [9, 10]}]},
            # Gate 2: Blocks path mid-way
            {"id": "gate_B", "pos": [{"type": "line", "start": [0, 13], "end": [10, 13]}]},
            # Gate 3: Blocks final approach to goal (was CDE)
            {"id": "gate_C", "pos": [{"type": "line", "start": [21, 16], "end": [21, 24]}]},
            # Gate 4: New gate replacing part of the static L-shape
            {"id": "gate_D", "pos": [{"type": "line", "start": [18, 18], "end": [18, 21]}]}
        ],
        "dynamic_wall_rules": [
            { "id": "gate_A", "type": "toggle", "inputs": ["A"] },
            { "id": "gate_B", "type": "toggle", "inputs": ["B"] },
            { "id": "gate_C", "type": "toggle", "inputs": ["C"] },
            { "id": "gate_D", "type": "toggle", "inputs": ["D"] } # E is now the red herring
        ]
    }

    # Expand walls
    expanded_walls = []
    for wall_def in base_env_config["walls"]:
        expanded_walls.extend(expand_line(wall_def))
    base_env_config["walls"] = expanded_walls

    # Expand dynamic walls
    expanded_dynamic_walls = []
    for wall_def in base_env_config["dynamic_walls"]:
        expanded_pos = []
        for pos_def in wall_def["pos"]:
            expanded_pos.extend(expand_line(pos_def))
        expanded_dynamic_walls.append({"id": wall_def["id"], "pos": expanded_pos})
    base_env_config["dynamic_walls"] = expanded_dynamic_walls

    # Define experiments
    experiments = []
    curiosity_levels = {
        "NoCuriosity": {"intrinsic_reward_weight": 0.0, "emotional_boost_factor": 0.0},
        "LowCuriosity": {"intrinsic_reward_weight": 0.02, "emotional_boost_factor": 0.2},
        "MediumCuriosity": {"intrinsic_reward_weight": 0.05, "emotional_boost_factor": 0.5}
    }

    for name, curiosity_params in curiosity_levels.items():
        params = base_parameters.copy()
        params.update(curiosity_params)
        params["environment_config"] = base_env_config
        
        experiments.append({
            "name": f"BalancedMaze_{name}",
            "runs": 1,
            "episodes_per_run": 500,
            "parameters": params
        })

    final_config = {
        "output_dir": "results/balanced_maze_test",
        "experiments": experiments
    }

    # Use a new filename to avoid confusion
    with open("experiments_balanced_maze_v2.json", 'w') as f:
        json.dump(final_config, f, indent=2)
    
    print("Successfully generated 'experiments_balanced_maze_v2.json'")

if __name__ == "__main__":
    generate_config()