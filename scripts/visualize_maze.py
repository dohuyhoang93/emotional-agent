
import json
import sys
import os

def print_maze(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
        
    # Assuming the first experiment
    exp = data['experiments'][0]
    env = exp['parameters']['environment_config']
    
    size = env.get('grid_size', 15)
    grid = [['.' for _ in range(size)] for _ in range(size)]
    
    # Static Walls
    for r, c in env.get('walls', []):
        if 0 <= r < size and 0 <= c < size:
            grid[r][c] = '#'
            
    # Dynamic Walls (Gates) - represented by 'D'
    for gate in env.get('dynamic_walls', []):
        for r, c in gate.get('pos', []):
            if 0 <= r < size and 0 <= c < size:
                grid[r][c] = 'D'
                
    # Switches - represented by 'S'
    for sw in env.get('logical_switches', []):
        r, c = sw.get('pos', [0, 0])
        if 0 <= r < size and 0 <= c < size:
            grid[r][c] = 'S'
            
    # Start - 'A'
    # Default to num_agents starts at [0,0] if not specified
    num_agents = env.get('num_agents', 1)
    starts = env.get('start_positions', [[0, 0]] * num_agents)
    for r, c in starts:
        if 0 <= r < size and 0 <= c < size:
            grid[r][c] = 'A'
            
    # Goal - 'G'
    gr, gc = env.get('goal_pos', [size - 1, size - 1])
    if 0 <= gr < size and 0 <= gc < size:
        grid[gr][gc] = 'G'
        
    # Print
    print(f"Maze Size: {size}x{size}")
    print("Legend: A=Start, G=Goal, #=Wall, D=Gate(Dynamic), S=Switch")
    print("   " + "".join([str(i%10) for i in range(size)]))
    for r in range(size):
        row_str = "".join(grid[r])
        print(f"{r:2d} {row_str}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        config = sys.argv[1]
    else:
        config = 'experiments.json'
    
    if os.path.exists(config):
        print_maze(config)
    else:
        print(f"File not found: {config}")
