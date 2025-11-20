import os
import copy

class GridWorld:
    """
    Môi trường Thế giới Lưới (Grid World) hỗ trợ nhiều tác nhân và Mê cung Logic Phức tạp.
    """
    def __init__(self, settings):
        print("Khởi tạo GridWorld đa tác nhân với Mê cung Logic Phức tạp...")
        
        env_config = settings.get("environment_config", {})
        self.size = env_config.get("grid_size", 15)
        
        # --- Thay đổi cho Đa tác nhân ---
        self.num_agents = env_config.get("num_agents", 1)
        default_starts = [[0, 0]] * self.num_agents
        self.start_positions = env_config.get("start_positions", default_starts)
        # --------------------------------

        self.goal_pos = tuple(env_config.get("goal_pos", [self.size - 1, self.size - 1]))
        
        self.static_walls = {tuple(w) for w in env_config.get("walls", [])}
        
        self.switches = {tuple(s['pos']): s['id'] for s in env_config.get("logical_switches", [])}
        self.dynamic_walls = {w['id']: [tuple(pos) for pos in w['pos']] for w in env_config.get("dynamic_walls", [])}
        self.dynamic_wall_rules = {rule['id']: rule for rule in env_config.get("dynamic_wall_rules", [])}
        
        self.max_steps = settings.get("max_steps_per_episode", 500)
        
        self.base_grid = self._create_base_grid()
        self.reset()

    def _create_base_grid(self):
        grid = [['.' for _ in range(self.size)] for _ in range(self.size)]
        if 0 <= self.goal_pos[0] < self.size and 0 <= self.goal_pos[1] < self.size:
            grid[self.goal_pos[0]][self.goal_pos[1]] = 'G'
        for r, c in self.static_walls:
            if 0 <= r < self.size and 0 <= c < self.size:
                grid[r][c] = '#'
        for r, c in self.switches.keys():
            if 0 <= r < self.size and 0 <= c < self.size and grid[r][c] == '.':
                grid[r][c] = 'S'
        return grid

    def _update_dynamic_walls(self):
        s = self.switch_states
        for wall_id, rule in self.dynamic_wall_rules.items():
            rule_type = rule.get("type")
            inputs = rule.get("inputs", [])
            is_closed = True
            if rule_type == "toggle":
                switch_id = inputs[0]
                is_closed = not s.get(switch_id, False)
            elif rule_type == "and":
                all_inputs_on = all(s.get(switch_id, False) for switch_id in inputs)
                is_closed = not all_inputs_on
            elif rule_type == "xor":
                if len(inputs) == 2:
                    input1_on = s.get(inputs[0], False)
                    input2_on = s.get(inputs[1], False)
                    is_closed = not (input1_on ^ input2_on)
            self.dynamic_wall_states[wall_id] = is_closed

    def reset(self):
        # --- Thay đổi cho Đa tác nhân ---
        self.agent_positions = {i: list(pos) for i, pos in enumerate(self.start_positions)}
        # --------------------------------
        self.current_step = 0
        self.switch_states = {switch_id: False for switch_id in self.switches.values()}
        self.dynamic_wall_states = {wall_id: True for wall_id in self.dynamic_walls.keys()}
        self._update_dynamic_walls()
        return self.get_all_observations()

    def get_observation(self, agent_id: int):
        # --- Thay đổi cho Đa tác nhân ---
        return {'agent_pos': tuple(self.agent_positions[agent_id])}

    def get_all_observations(self):
        # --- Hàm mới cho Đa tác nhân ---
        return {i: self.get_observation(i) for i in range(self.num_agents)}

    def perform_action(self, agent_id: int, action: str):
        # --- Thay đổi cho Đa tác nhân ---
        # self.current_step += 1 # Xóa dòng này, việc tăng step sẽ do main.py quản lý
        
        r, c = self.agent_positions[agent_id]
        if action == 'up': r -= 1
        elif action == 'down': r += 1
        elif action == 'left': c -= 1
        elif action == 'right': c += 1
        new_pos = (r, c)

        is_valid_move = True
        if not (0 <= r < self.size and 0 <= c < self.size):
            is_valid_move = False
        elif new_pos in self.static_walls:
            is_valid_move = False
        else:
            for wall_id, is_closed in self.dynamic_wall_states.items():
                if is_closed and new_pos in self.dynamic_walls.get(wall_id, []):
                    is_valid_move = False
                    break
        
        if is_valid_move:
            self.agent_positions[agent_id] = list(new_pos)
            if tuple(self.agent_positions[agent_id]) in self.switches:
                switch_id = self.switches[tuple(self.agent_positions[agent_id])]
                if switch_id in self.switch_states:
                    self.switch_states[switch_id] = not self.switch_states[switch_id]
                    self._update_dynamic_walls()
        else:
            return -0.5

        if tuple(self.agent_positions[agent_id]) == self.goal_pos:
            return 10.0
        if self.is_done(): # Kiểm tra is_done() thay vì chỉ current_step
            return -2.0
        return -0.1
        # --------------------------------

    def is_done(self):
        # --- Thay đổi cho Đa tác nhân ---
        # Kết thúc nếu BẤT KỲ agent nào đến đích, hoặc hết thời gian
        any_agent_at_goal = any(tuple(pos) == self.goal_pos for pos in self.agent_positions.values())
        return any_agent_at_goal or self.current_step >= self.max_steps
        # --------------------------------

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Step: {self.current_step}/{self.max_steps}")
        render_grid = copy.deepcopy(self.base_grid)
        for wall_id, is_closed in self.dynamic_wall_states.items():
            if is_closed:
                for r, c in self.dynamic_walls.get(wall_id, []):
                    if 0 <= r < self.size and 0 <= c < self.size and render_grid[r][c] == '.':
                        render_grid[r][c] = '%'
        
        # --- Thay đổi cho Đa tác nhân ---
        for agent_id, pos in self.agent_positions.items():
            r, c = pos
            # Hiển thị agent bằng số ID của nó
            agent_char = str(agent_id)
            if render_grid[r][c] in ['.', 'S']:
                render_grid[r][c] = agent_char
        # --------------------------------

        for row in render_grid:
            print(' '.join(row))
        print("-" * 20)
        print("Switch States:", {k: "ON" if v else "OFF" for k, v in self.switch_states.items()})
