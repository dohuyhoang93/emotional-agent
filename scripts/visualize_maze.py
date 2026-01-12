
import json
import sys

def print_maze(config_path):
    with open(config_path, 'r') as f:
        data = json.load(f)
        
    # Assuming the first experiment
    exp = data['experiments'][0]
    env = exp['parameters']['environment_config']
    
    size = env['grid_size']
    grid = [['.' for _ in range(size)] for _ in range(size)]
    
    # Static Walls
    for r, c in env['walls']:
        if 0 <= r < size and 0 <= c < size:
            grid[r][c] = '#'
            
    # Dynamic Walls (Gates) - represented by 'D'
    for gate in env['dynamic_walls']:
        for r, c in gate['pos']:
            if 0 <= r < size and 0 <= c < size:
                grid[r][c] = 'D'
                
    # Switches - represented by 'S'
    for sw in env['logical_switches']:
        r, c = sw['pos']
        if 0 <= r < size and 0 <= c < size:
            grid[r][c] = 'S'
            
    # Start - 'A'
    for r, c in env['start_positions']:
        if 0 <= r < size and 0 <= c < size:
            grid[r][c] = 'A'
            
    # Goal - 'G'
    gr, gc = env['goal_pos']
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
    print_maze('experiments.json')
