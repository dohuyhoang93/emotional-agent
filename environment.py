import os

class GridWorld:
    """
    Môi trường Thế giới Lưới (Grid World) được tạo động từ settings.
    Tác nhân (A) phải di chuyển từ vị trí bắt đầu đến mục tiêu (G).
    '#' là tường. '.' là đường đi.
    """
    def __init__(self, settings):
        print("Khởi tạo GridWorld động...")
        
        # Lấy các cấu hình môi trường từ settings
        env_config = settings.get("environment_config", {})
        self.size = env_config.get("grid_size", 5)
        self.start_pos = tuple(env_config.get("start_pos", [0, 0]))
        self.goal_pos = tuple(env_config.get("goal_pos", [self.size - 1, self.size - 1]))
        walls = env_config.get("walls", [])
        
        # Ghi đè các tham số nếu chúng tồn tại ở cấp cao nhất (cho tương thích ngược)
        self.size = settings.get("grid_size", self.size)
        self.start_pos = tuple(settings.get("start_pos", self.start_pos))
        self.goal_pos = tuple(settings.get("goal_pos", self.goal_pos))
        walls = settings.get("walls", walls)

        self.max_steps = settings.get("max_steps_per_episode", 25)
        self.agent_pos = list(self.start_pos)
        self.current_step = 0

        # Tạo lưới một cách linh động
        self.grid = [['.' for _ in range(self.size)] for _ in range(self.size)]
        
        # Đặt mục tiêu
        goal_r, goal_c = self.goal_pos
        if 0 <= goal_r < self.size and 0 <= goal_c < self.size:
            self.grid[goal_r][goal_c] = 'G'

        # Đặt tường
        for r, c in walls:
            if 0 <= r < self.size and 0 <= c < self.size:
                self.grid[r][c] = '#'

    def reset(self):
        """Reset môi trường về trạng thái ban đầu."""
        self.agent_pos = list(self.start_pos)
        self.current_step = 0
        # print("Môi trường: Đã reset.") # Tắt để đỡ rối console khi chạy orchestrator
        return self.get_observation()

    def get_observation(self):
        """Quan sát là tọa độ của tác nhân."""
        return {'agent_pos': tuple(self.agent_pos)}

    def perform_action(self, action: str):
        """Thực hiện hành động và trả về phần thưởng ngoại sinh."""
        self.current_step += 1
        
        r, c = self.agent_pos
        if action == 'up':
            r -= 1
        elif action == 'down':
            r += 1
        elif action == 'left':
            c -= 1
        elif action == 'right':
            c += 1

        # Kiểm tra va chạm và cập nhật vị trí
        if 0 <= r < self.size and 0 <= c < self.size and self.grid[r][c] != '#':
            self.agent_pos = [r, c]
        else:
            # Va vào tường hoặc ra ngoài, không di chuyển và bị phạt
            return -0.5

        # Kiểm tra trạng thái kết thúc
        if tuple(self.agent_pos) == self.goal_pos:
            return 10.0  # Phần thưởng lớn khi đến đích
        
        if self.current_step >= self.max_steps:
            return -2.0 # Phạt nặng nếu hết lượt

        return -0.1 # Phạt nhẹ cho mỗi bước đi để khuyến khích hiệu quả

    def is_done(self):
        """Kiểm tra xem episode đã kết thúc chưa."""
        return tuple(self.agent_pos) == self.goal_pos or self.current_step >= self.max_steps

    def render(self):
        """Hiển thị trạng thái hiện tại của lưới."""
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"Step: {self.current_step}/{self.max_steps}")
        temp_grid = [row[:] for row in self.grid]
        r, c = self.agent_pos
        
        # Đảm bảo agent không vẽ đè lên mục tiêu
        if temp_grid[r][c] == '.':
            temp_grid[r][c] = 'A'
        
        for row in temp_grid:
            print(' '.join(row))
        print("-" * 10)
