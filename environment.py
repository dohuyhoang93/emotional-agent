import os

class GridWorld:
    """
    Môi trường Thế giới Lưới (Grid World).
    Tác nhân (A) phải di chuyển từ vị trí bắt đầu đến mục tiêu (G).
    '#' là tường. '.' là đường đi.
    """
    def __init__(self, settings):
        print("Khởi tạo GridWorld...")
        self.grid = [
            ['.', '.', '.', '#', '.'],
            ['.', '#', '.', '.', '.'],
            ['.', '.', '#', 'G', '.'],
            ['A', '.', '.', '.', '.'],
            ['.', '#', '.', '.', '.']
        ]
        self.size = len(self.grid)
        self.start_pos = self._find_char('A')
        self.agent_pos = list(self.start_pos)
        self.goal_pos = self._find_char('G')
        self.max_steps = settings.get("max_steps_per_episode", 25)
        self.current_step = 0

    def _find_char(self, char):
        for r, row in enumerate(self.grid):
            for c, val in enumerate(row):
                if val == char:
                    return (r, c)
        return None

    def reset(self):
        """Reset môi trường về trạng thái ban đầu."""
        self.agent_pos = list(self.start_pos)
        self.current_step = 0
        print("Môi trường: Đã reset.")
        return self.get_observation()

    def get_observation(self):
        """Quan sát là tọa độ của tác nhân."""
        return {'agent_pos': tuple(self.agent_pos)}

    def perform_action(self, action: str):
        """Thực hiện hành động và trả về phần thưởng ngoại sinh."""
        self.current_step += 1
        
        # Tính toán vị trí mới
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
        # Xóa màn hình console để hiển thị sạch sẽ
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print(f"Step: {self.current_step}/{self.max_steps}")
        temp_grid = [row[:] for row in self.grid]
        r, c = self.agent_pos
        if temp_grid[r][c] == '.':
            temp_grid[r][c] = 'A'
        
        for row in temp_grid:
            print(' '.join(row))
        print("-" * 10)