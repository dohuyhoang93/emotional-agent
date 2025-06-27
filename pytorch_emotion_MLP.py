import torch
import torch.nn as nn
import torch.nn.functional as F

class EmotionToWeightMLP(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(7, 16)
        self.fc2 = nn.Linear(16, 3)

    def forward(self, emotion_vector):
        x = F.relu(self.fc1(emotion_vector))
        return torch.sigmoid(self.fc2(x))  # Output 3 trọng số: [w1, w2, w3]

class EmotionalAgent:
    def __init__(self):
        self.emotions = {
            "vui": 0.5, "buồn": 0.2, "giận": 0.1, "lo lắng": 0.3,
            "sợ": 0.2, "thoải mái": 0.6, "ghen": 0.1
        }
        self.needs = {"safety": 0.7, "esteem": 0.6, "love": 0.8}
        self.model = EmotionToWeightMLP()

    def update_weights(self):
        e_vector = torch.tensor(list(self.emotions.values()), dtype=torch.float32)
        weights = self.model(e_vector).detach().numpy()
        return weights

    def objective_function(self):
        weights = self.update_weights()
        return (weights[0] * self.needs["safety"] +
                weights[1] * self.needs["esteem"] +
                weights[2] * self.needs["love"])

    def update_emotions(self, event):
        if event == "threat":
            self.emotions["sợ"] = min(1.0, self.emotions["sợ"] + 0.3)
            self.emotions["lo lắng"] = min(1.0, self.emotions["lo lắng"] + 0.2)
        elif event == "praise":
            self.emotions["vui"] = min(1.0, self.emotions["vui"] + 0.4)
            self.emotions["thoải mái"] = min(1.0, self.emotions["thoải mái"] + 0.3)

# Thử nghiệm
agent = EmotionalAgent()
print("Objective ban đầu:", agent.objective_function())
agent.update_emotions("threat")
print("Objective sau threat:", agent.objective_function())

# pip install torch --index-url https://download.pytorch.org/whl/cpu
# pip install torch