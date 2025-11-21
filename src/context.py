import torch

class AgentContext:
    """
    Dữ liệu Ngữ cảnh (Context Data) cho tác nhân.
    Đây là một cấu trúc dữ liệu "câm", không chứa logic hay phương thức.
    """
    def __init__(self, settings: dict):
        # Các vector trạng thái nội tại
        self.N_vector: torch.Tensor = torch.tensor(settings['initial_needs'], dtype=torch.float32)
        self.E_vector: torch.Tensor = torch.tensor(settings['initial_emotions'], dtype=torch.float32)
        self.confidence: float = 0.0 # Tách riêng để dễ truy cập, là E_vector[0]

        # Bộ nhớ
        self.short_term_memory: list = []
        self.long_term_memory: dict = {}

        # Chính sách và Hành động
        self.policy: dict = {
            'exploration_rate': settings.get('initial_exploration', 1.0),
            'min_exploration': settings.get('min_exploration', 0.05)
        }
        # Các tham số cho logic khám phá mới
        self.base_exploration_rate: float = settings.get('initial_exploration', 1.0)
        self.base_exploration_decay: float = settings.get('exploration_decay', 0.995)
        self.emotional_boost_factor: float = settings.get('emotional_boost_factor', 0.5)

        self.selected_action = None

        # Dữ liệu từ môi trường
        self.current_observation = None
        self.previous_observation = None
        self.last_reward: dict = {'extrinsic': 0.0, 'intrinsic': 0.0}

        # Các thành phần cho việc học
        self.q_table: dict = {}
        self.learning_rate: float = settings.get('learning_rate', 0.1)
        self.discount_factor: float = settings.get('discount_factor', 0.95)
        self.td_error: float = 0.0 # Lỗi chênh lệch thời gian, dùng làm thước đo "ngạc nhiên"
        
        # Các thành phần cho việc học của MLP Cảm xúc
        self.emotion_model = None
        self.emotion_optimizer = None
        self.intrinsic_reward_weight: float = settings.get('intrinsic_reward_weight', 0.1)
        self.use_dynamic_curiosity: bool = settings.get('use_dynamic_curiosity', False)

        # --- Chỉ số hệ thống ---
        self.last_cycle_time: float = 0.0
        self.max_steps: int = settings.get('max_steps', 0)
        self.log_level: str = "info" # Added log_level to AgentContext

        # --- Trạng thái niềm tin về thế giới ---
        # Vị trí các công tắc, ví dụ: {'A': (1, 8), ...}
        self.switch_locations: dict = settings.get('switch_locations', {}) 
        # Niềm tin về trạng thái các công tắc, ví dụ: {'A': False, 'B': True, ...}
        self.believed_switch_states: dict = {switch_id: False for switch_id in "ABCD"}


    def get_composite_state(self, agent_pos: tuple) -> tuple:
        """
        Tạo ra một "trạng thái phức hợp" đầy đủ bằng cách kết hợp vị trí của agent
        với niềm tin về trạng thái của các công tắc.
        Đây sẽ là key cho Q-table.
        """
        # Lấy trạng thái của các công tắc theo thứ tự alphabet để đảm bảo nhất quán
        switch_states = tuple(self.believed_switch_states[key] for key in sorted(self.believed_switch_states.keys()))
        return agent_pos + switch_states

    def __str__(self):
        # Giả sử E_vector[0] là 'tin cậy' (confidence)
        return (
            f"  Believed Switches: {{'A': {self.believed_switch_states['A']}, 'B': {self.believed_switch_states['B']}, 'C': {self.believed_switch_states['C']}, 'D': {self.believed_switch_states['D']}}}\n"
            f"  Confidence: {self.confidence:.3f}\n"
            f"  Policy: exploration_rate={self.policy['exploration_rate']:.3f} (base={self.base_exploration_rate:.3f})\n"
            f"  Last TD Error: {self.td_error:.3f}"
        )

