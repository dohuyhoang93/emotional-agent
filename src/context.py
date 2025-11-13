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

        # Bộ nhớ
        self.short_term_memory: list = []
        self.long_term_memory: dict = {}

        # Chính sách và Hành động
        self.policy: dict = {
            'exploration_rate': settings['initial_exploration'],
            'exploration_decay': settings['exploration_decay'],
            'min_exploration': settings['min_exploration']
        }
        self.selected_action = None

        # Dữ liệu từ môi trường
        self.current_observation = None
        self.previous_observation = None
        self.last_reward: dict = {'extrinsic': 0.0, 'intrinsic': 0.0}

        # Các thành phần cho việc học
        self.q_table: dict = {}
        self.learning_rate: float = settings['learning_rate']
        self.discount_factor: float = settings['discount_factor']
        self.td_error: float = 0.0 # Lỗi chênh lệch thời gian, dùng làm thước đo "ngạc nhiên"
        
        # Các thành phần cho việc học của MLP Cảm xúc
        self.emotion_model = None
        self.emotion_optimizer = None
        self.intrinsic_reward_weight: float = settings['intrinsic_reward_weight']


    def __str__(self):
        # Giả sử E_vector[0] là 'tin cậy', E_vector[1] là 'ngạc nhiên'
        return (
            f"  E_vector: [tin cậy: {self.E_vector.detach().numpy()[0]:.3f}, ngạc nhiên: {self.E_vector.detach().numpy()[1]:.3f}, ...]\n"
            f"  Policy: exploration_rate={self.policy['exploration_rate']:.3f}\n"
            f"  Last TD Error: {self.td_error:.3f}"
        )

