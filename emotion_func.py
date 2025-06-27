class EmotionalAgent:
    def __init__(self):
        # Vector cảm xúc ban đầu
        self.emotions = {
            "vui": 0.5, "buồn": 0.2, "giận": 0.1, "lo lắng": 0.3,
            "sợ": 0.2, "thoải mái": 0.6, "ghen": 0.1
        }
        # Giá trị nhu cầu ban đầu
        self.needs = {"safety": 0.7, "esteem": 0.6, "love": 0.8}
        # Ma trận ánh xạ cảm xúc -> trọng số
        self.mapping_matrix = [
            [0.1, -0.1, 0.0, 0.5, 0.6, 0.3, 0.0],  # Safety
            [0.4, -0.3, 0.5, 0.1, 0.0, 0.2, 0.4],  # Esteem
            [0.5, -0.4, 0.1, 0.0, 0.0, 0.3, 0.3]   # Love
        ]

    def update_weights(self):
        # Tính trọng số từ cảm xúc
        weights = [0, 0, 0]
        emotion_values = list(self.emotions.values())
        for i in range(3):
            weights[i] = sum(self.mapping_matrix[i][j] * emotion_values[j] for j in range(7))
            weights[i] = max(0, min(1, weights[i]))  # Giới hạn 0-1
        return weights

    def objective_function(self):
        weights = self.update_weights()
        return (weights[0] * self.needs["safety"] +
                weights[1] * self.needs["esteem"] +
                weights[2] * self.needs["love"])

    def update_emotions(self, event):
        # Cập nhật cảm xúc dựa trên sự kiện (giả lập)
        if event == "threat":
            self.emotions["sợ"] += 0.3
            self.emotions["lo lắng"] += 0.2
        elif event == "praise":
            self.emotions["vui"] += 0.4
            self.emotions["thoải mái"] += 0.3

# Thử nghiệm
agent = EmotionalAgent()
print("Objective ban đầu:", agent.objective_function())
agent.update_emotions("threat")
print("Objective sau threat:", agent.objective_function())