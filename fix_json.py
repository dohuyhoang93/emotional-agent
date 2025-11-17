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

def fix_json_walls(file_path):
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return

    for exp in config.get("experiments", []):
        env_config = exp.get("parameters", {}).get("environment_config", {})
        if not env_config:
            continue

        # Expand static walls
        if "walls" in env_config and isinstance(env_config["walls"][0], dict):
            new_static_walls = []
            for wall_def in env_config["walls"]:
                new_static_walls.extend(expand_line(wall_def))
            env_config["walls"] = new_static_walls

        # Expand dynamic walls
        if "dynamic_walls" in env_config and isinstance(env_config["dynamic_walls"][0]["pos"][0], dict):
            new_dynamic_walls = []
            for wall_def in env_config["dynamic_walls"]:
                expanded_pos = []
                for pos_def in wall_def["pos"]:
                    expanded_pos.extend(expand_line(pos_def))
                new_dynamic_walls.append({"id": wall_def["id"], "pos": expanded_pos})
            env_config["dynamic_walls"] = new_dynamic_walls
    
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Successfully fixed walls in {file_path}")
    except Exception as e:
        print(f"Error writing to {file_path}: {e}")

if __name__ == "__main__":
    fix_json_walls("experiments_forked_path.json")
