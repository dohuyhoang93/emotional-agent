import json
import numpy as np

def visualize_maze():
    with open('experiments.json', 'r') as f:
        config = json.load(f)
    
    # Tìm experiment multi_agent_complex_maze
    maze_config = None
    for exp in config['experiments']:
        if exp['name'] == 'multi_agent_complex_maze':
            maze_config = exp['parameters']['environment_config']
            break
    
    if not maze_config:
        print("Không tìm thấy cấu hình maze.")
        return

    size = maze_config['grid_size']
    grid = np.full((size, size), '.')
    
    # Goal
    gx, gy = maze_config['goal_pos']
    grid[gx, gy] = 'G'
    
    # Static Walls
    for wx, wy in maze_config['walls']:
        grid[wx, wy] = '#'
        
    # Switches
    for s in maze_config['logical_switches']:
        sx, sy = s['pos']
        grid[sx, sy] = 'S'
        
    # Dynamic Walls (Gates)
    for dw in maze_config['dynamic_walls']:
        for dx, dy in dw['pos']:
            grid[dx, dy] = '%'
            
    # Starts
    for idx, (sx, sy) in enumerate(maze_config['start_positions']):
        grid[sx, sy] = str(idx)

    print(f"Maze Size: {size}x{size}")
    print("Ký hiệu: #=Tường tĩnh, %=Cổng động (Gate), S=Công tắc (Switch), G=Đích, 0-4=Agents")
    print("\n" + " ".join([str(i%10) for i in range(size)]))
    for i, row in enumerate(grid):
        print(" ".join(row) + f"  {i}")

if __name__ == "__main__":
    visualize_maze()
