from typing import Dict, Any, Tuple
from environment import GridWorld

class EnvironmentAdapter:
    """
    Adapter wrap lấy Environment object (GridWorld).
    Mục tiêu: Cung cấp interface chuẩn cho các Process, tuân thủ nguyên tắc Dependency Inversion (ở mức nhẹ).
    """
    def __init__(self, env: GridWorld):
        self.env = env

    def get_observation(self, agent_id: int) -> Dict[str, Any]:
        """
        Lấy observation thô từ môi trường.
        Output trả về là một Dict chứa trạng thái vật lý.
        
        DEPRECATED: Sẽ chuyển sang get_sensor_vector()
        """
        return self.env.get_observation(agent_id)
    
    def get_sensor_vector(self, agent_id: int):
        """
        Lấy sensor vector 16-dim từ môi trường.
        
        Returns:
            np.ndarray shape (16,)
        """
        return self.env.get_sensor_vector(agent_id)

    def perform_action(self, agent_id: int, action: str) -> float:
        """
        Thực thi hành động vật lý.
        WARNING: Đây là hàm gây Side-Effect lên môi trường.
        Output: Reward từ môi trường.
        """
        return self.env.perform_action(agent_id, action)

    def is_done(self) -> bool:
        return self.env.is_done()

    def get_reward_signals(self, agent_id: int) -> Dict[str, bool]:
        """
        (Optional) Lấy các tín hiệu thưởng trực tiếp nếu môi trường cung cấp.
        Hiện tại GridWorld trả về reward qua logic trong main.py, nhưng adapter nên support.
        """
        # Placeholder nếu cần
        return {}
