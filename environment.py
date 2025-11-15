import os
import copy

class GridWorld:
    """
    Môi trường Thế giới Lưới (Grid World) hỗ trợ Mê cung Logic Phức tạp.
    Các quy tắc của tường động được mã hóa cứng trong `_update_dynamic_walls`.
    """
    def __init__(self, settings):
        print("Khởi tạo GridWorld động với Mê cung Logic Phức tạp...")
        
        env_config = settings.get("environment_config", {})
        self.size = env_config.get("grid_size", 15)
        self.start_pos = tuple(env_config.get("start_pos", [0, 0]))
        self.goal_pos = tuple(env_config.get("goal_pos", [self.size - 1, self.size - 1]))
        
        self.static_walls = {tuple(w) for w in env_config.get("walls", [])}
        
        # --- Logic cho Mê cung Logic ---
        # Ánh xạ vị trí tới ID công tắc, ví dụ: (1, 8) -> 'A'
        self.switches = {tuple(s['pos']): s['id'] for s in env_config.get("logical_switches", [])}
        # Ánh xạ ID tường tới danh sách vị trí, ví dụ: 'wall_A' -> [(y,x), ...]
        self.dynamic_walls = {w['id']: [tuple(pos) for pos in w['pos']] for w in env_config.get("dynamic_walls", [])}
        
        self.max_steps = settings.get("max_steps_per_episode", 500)
        
        self.base_grid = self._create_base_grid()
        self.reset()

    def _create_base_grid(self):
        """Tạo lưới tĩnh ban đầu (đường đi, mục tiêu, tường tĩnh, công tắc)."""
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
        """
        Cập nhật trạng thái của các tường động dựa trên trạng thái công tắc.
        Đây là nơi chứa toàn bộ logic phức tạp của mê cung.
        NOTE: Trạng thái tường là True nếu BỊ ĐÓNG, False nếu MỞ.
        """
        s = self.switch_states
        
        # Các quy tắc logic cho từng bức tường
        # Tường A và B là công tắc đơn giản
        self.dynamic_wall_states['wall_A'] = not s.get('A', False)
        self.dynamic_wall_states['wall_B'] = not s.get('B', False)
        
        # Tường C là cổng AND: Đóng trừ khi A và B đều Bật
        self.dynamic_wall_states['wall_C'] = not (s.get('A', False) and s.get('B', False))
        
        # Tường D là cổng XOR: Đóng trừ khi chỉ một trong C hoặc D được Bật
        self.dynamic_wall_states['wall_D'] = not (s.get('C', False) ^ s.get('D', False))

    def reset(self):
        """Reset môi trường, bao gồm cả trạng thái công tắc và tường động."""
        self.agent_pos = list(self.start_pos)
        self.current_step = 0
        
        # Reset trạng thái công tắc (False = TẮT)
        self.switch_states = {switch_id: False for switch_id in "ABCD"}
        
        # Reset trạng thái tường động (True = ĐÓNG)
        self.dynamic_wall_states = {wall_id: True for wall_id in self.dynamic_walls.keys()}
        
        # Cập nhật trạng thái tường ban đầu dựa trên trạng thái công tắc ban đầu
        self._update_dynamic_walls()
        
        return self.get_observation()

    def get_observation(self):
        """Quan sát là tọa độ của tác nhân."""
        return {'agent_pos': tuple(self.agent_pos)}

    def perform_action(self, action: str):
        """Thực hiện hành động, kiểm tra va chạm và kích hoạt công tắc."""
        self.current_step += 1
        
        r, c = self.agent_pos
        if action == 'up': r -= 1
        elif action == 'down': r += 1
        elif action == 'left': c -= 1
        elif action == 'right': c += 1

        new_pos = (r, c)

        # Kiểm tra va chạm
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
            self.agent_pos = list(new_pos)
            # Kích hoạt công tắc nếu đi vào
            if tuple(self.agent_pos) in self.switches:
                switch_id = self.switches[tuple(self.agent_pos)]
                self.switch_states[switch_id] = not self.switch_states[switch_id]
                # Cập nhật lại toàn bộ logic tường động sau khi một công tắc thay đổi
                self._update_dynamic_walls()
        else:
            return -0.5

        if tuple(self.agent_pos) == self.goal_pos:
            return 10.0
        
        if self.current_step >= self.max_steps:
            return -2.0

        return -0.1

    def is_done(self):
        return tuple(self.agent_pos) == self.goal_pos or self.current_step >= self.max_steps

    def render(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"Step: {self.current_step}/{self.max_steps}")
        
        render_grid = copy.deepcopy(self.base_grid)
        for wall_id, is_closed in self.dynamic_wall_states.items():
            if is_closed:
                for r, c in self.dynamic_walls.get(wall_id, []):
                    if 0 <= r < self.size and 0 <= c < self.size and render_grid[r][c] == '.':
                        render_grid[r][c] = '%'

        r, c = self.agent_pos
        if render_grid[r][c] in ['.', 'S']:
            render_grid[r][c] = 'A'
        
        for row in render_grid:
            print(' '.join(row))
        print("-" * 20)
        print("Switch States:", {k: "ON" if v else "OFF" for k, v in self.switch_states.items()})
        # print("Wall States:", {k: "CLOSED" if v else "OPEN" for k, v in self.dynamic_wall_states.items()})
