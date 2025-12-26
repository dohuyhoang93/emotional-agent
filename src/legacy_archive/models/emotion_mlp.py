import torch
import torch.nn as nn

class EmotionCalculatorMLP(nn.Module):
    """
    MLP để tính toán Vector Cảm xúc Máy (E_vector).
    Input: Nối của N_vector, B_vector (trạng thái môi trường), m_vector (trạng thái bộ nhớ).
    Output: E_vector mới.
    """
    def __init__(self, n_dim, b_dim, m_dim, e_dim):
        super().__init__()
        input_dim = n_dim + b_dim + m_dim
        self.fc1 = nn.Linear(input_dim, 16)
        self.fc2 = nn.Linear(16, 16)
        self.fc3 = nn.Linear(16, e_dim)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.sigmoid(self.fc3(x)) # Giữ giá trị E_vector trong khoảng [0, 1]
        return x
