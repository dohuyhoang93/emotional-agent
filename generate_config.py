import json
import os

class MazeConfigBuilder:
    def __init__(self, grid_size=25, max_steps=500):
        self.config = {
            "grid_size": grid_size,
            "num_agents": 1,
            "start_positions": [[0, 0]],
            "goal_pos": [grid_size-1, grid_size-1],
            "max_steps_per_episode": max_steps,
            "walls": [],
            "logical_switches": [],
            "dynamic_walls": [],
            "dynamic_wall_rules": []
        }
        self.next_switch_id = 0

    def set_agents(self, num_agents, start_positions=None):
        self.config["num_agents"] = num_agents
        if start_positions:
            if len(start_positions) != num_agents:
                raise ValueError("Number of start positions must match num_agents")
            self.config["start_positions"] = start_positions
        else:
            # Default: all start at [0,0]
            self.config["start_positions"] = [[0, 0] for _ in range(num_agents)]
        return self

    def set_goal(self, pos):
        self.config["goal_pos"] = pos
        return self

    def add_wall_line(self, start, end):
        """Adds a line of walls from start to end (inclusive)."""
        coords = self._expand_line(start, end)
        self.config["walls"].extend(coords)
        return self

    def add_switch(self, pos, switch_id=None):
        if switch_id is None:
            switch_id = chr(ord('A') + self.next_switch_id)
            self.next_switch_id += 1
        
        self.config["logical_switches"].append({
            "pos": pos,
            "id": switch_id
        })
        return switch_id

    def add_dynamic_wall(self, wall_id, start, end, rule_type="toggle", inputs=None):
        """
        Adds a dynamic wall (gate) with a logic rule.
        rule_type: 'toggle', 'and', 'xor'
        inputs: list of switch_ids
        """
        coords = self._expand_line(start, end)
        
        # Add definition
        self.config["dynamic_walls"].append({
            "id": wall_id,
            "pos": coords
        })
        
        # Add rule
        if inputs is None:
            raise ValueError("Inputs (switch IDs) must be provided for dynamic walls")
            
        self.config["dynamic_wall_rules"].append({
            "id": wall_id,
            "type": rule_type,
            "inputs": inputs
        })
        return self

    def _expand_line(self, start, end):
        coords = []
        y1, x1 = start
        y2, x2 = end

        if y1 == y2: # Horizontal
            for x in range(min(x1, x2), max(x1, x2) + 1):
                coords.append([y1, x])
        elif x1 == x2: # Vertical
            for y in range(min(y1, y2), max(y1, y2) + 1):
                coords.append([y, x1])
        else:
            # Simple diagonal or arbitrary line (Bresenham's could be used here, but keeping it simple)
            # For now, just support orthogonal lines or single points
            coords.append(start)
            if start != end:
                coords.append(end)
        return coords

    def build(self):
        # Remove duplicates in walls
        self.config["walls"] = [list(x) for x in set(tuple(x) for x in self.config["walls"])]
        return self.config

def generate_complex_maze_config():
    """Recreates the 'Complex Maze' used in Run 95 but using the Builder."""
    builder = MazeConfigBuilder(grid_size=25, max_steps=500)
    
    # 1. Agents
    builder.set_agents(num_agents=5, start_positions=[
        [0, 0], [0, 1], [1, 0], [2, 0], [0, 2]
    ])
    
    # 2. Static Walls (The 'Cages')
    # Cage 1 (Top Left)
    builder.add_wall_line([0, 5], [8, 5])
    builder.add_wall_line([8, 5], [8, 10])
    
    # Cage 2 (Middle)
    builder.add_wall_line([12, 0], [12, 8])
    builder.add_wall_line([12, 8], [20, 8])
    builder.add_wall_line([20, 0], [20, 8]) # Encloses the bottom left area
    
    # Cage 3 (Right Barrier)
    builder.add_wall_line([5, 15], [15, 15])
    
    # Cage 4 (Goal Area Protection)
    builder.add_wall_line([22, 18], [24, 18])
    builder.add_wall_line([18, 22], [18, 24])
    
    # 3. Switches
    sw_A = builder.add_switch([1, 1], "A")
    sw_B = builder.add_switch([10, 2], "B")
    sw_C = builder.add_switch([15, 12], "C")
    sw_D = builder.add_switch([16, 20], "D")
    sw_E = builder.add_switch([22, 22], "E")
    
    # 4. Dynamic Walls (Gates)
    # Gate A: Blocks exit from start
    builder.add_dynamic_wall("gate_A", [9, 0], [9, 10], rule_type="toggle", inputs=[sw_A])
    
    # Gate B: Blocks middle passage
    builder.add_dynamic_wall("gate_B", [0, 13], [10, 13], rule_type="toggle", inputs=[sw_B])
    
    # Gate C: Blocks path to goal area
    builder.add_dynamic_wall("gate_C", [21, 16], [21, 24], rule_type="toggle", inputs=[sw_C])
    
    # Gate D: The final hurdle
    builder.add_dynamic_wall("gate_D", [18, 18], [18, 21], rule_type="toggle", inputs=[sw_D])
    
    # Example of AND gate (not in original run, but showing capability)
    # builder.add_dynamic_wall("gate_Special", [5, 5], [5, 6], rule_type="and", inputs=[sw_A, sw_B])
    
    return builder.build()

def generate_logic_test_config():
    """Creates a 25x25 maze specifically to test AND and XOR gates."""
    builder = MazeConfigBuilder(grid_size=25, max_steps=500)
    
    # 1. Agents (Same as Complex Maze)
    builder.set_agents(num_agents=5, start_positions=[
        [0, 0], [0, 1], [1, 0], [2, 0], [0, 2]
    ])
    
    # 2. Switches
    sw_A = builder.add_switch([2, 2], "A")
    sw_B = builder.add_switch([2, 4], "B")
    sw_C = builder.add_switch([10, 10], "C")
    sw_D = builder.add_switch([10, 12], "D")
    
    # 3. Logic Gates
    
    # AND Gate: Requires BOTH A and B to be ON to open
    # Blocks the path out of the starting zone
    builder.add_wall_line([5, 0], [5, 5]) # Static wall part
    builder.add_dynamic_wall("gate_AND", [5, 2], [5, 3], rule_type="and", inputs=[sw_A, sw_B])
    
    # XOR Gate: Requires EITHER C or D (but not both) to be ON to open
    # Blocks the path to the goal
    builder.add_wall_line([15, 0], [15, 24]) # Long static wall
    builder.add_dynamic_wall("gate_XOR", [15, 11], [15, 13], rule_type="xor", inputs=[sw_C, sw_D])
    
    return builder.build()

def main():
    # 1. Generate Environment Config
    # env_config = generate_complex_maze_config()
    env_config = generate_logic_test_config() # Switch to Logic Test Config
    
    # 2. Define Experiment Parameters
    experiment_params = {
        "use_dynamic_curiosity": True,
        "use_adaptive_fatigue": True,
        "fatigue_growth_rate": 5.0,
        "emotional_boost_factor": 0.4,
        "short_term_memory_limit": 100,
        "assimilation_rate": 0.3,
        "intrinsic_reward_weight": 0.05,
        "initial_exploration": 1.0,
        "min_exploration": 0.05,
        "exploration_decay": 0.9995,
        "visual_mode": False,
        "environment_config": env_config
    }
    
    # 3. Create Full Config Structure
    full_config = {
        "output_dir": "results/logic_test_run",
        "log_level": "silent",
        "experiments": [
            {
                "name": "LogicGate_Test_Run",
                "runs": 1,
                "episodes_per_run": 1000, # Short run for testing
                "log_level": "silent",
                "parameters": experiment_params
            }
        ]
    }
    
    # 4. Save to JSON
    output_file = "experiments_logic_test.json"
    with open(output_file, 'w') as f:
        json.dump(full_config, f, indent=4)
    
    print(f"Successfully generated '{output_file}' with AND/XOR logic gates.")


if __name__ == "__main__":
    main()