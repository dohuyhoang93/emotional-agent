import numpy as np

np.random.seed(42)

# Simulate prototypes for 1024 neurons
N = 1024
D = 16
protos = np.random.randn(N, D)
protos = protos / np.linalg.norm(protos, axis=1, keepdims=True)

# Simulate sensor vector (2 coordinates are 1.0)
sensor = np.zeros(D)
sensor[0] = 1.0
sensor[8] = 1.0
sensor = sensor / np.linalg.norm(sensor)

sim = np.matmul(protos, sensor)
sim = np.maximum(0, sim)

sim_pow1 = sim
sim_pow2 = sim ** 2
sim_pow3 = sim ** 3

amp = 5.0
thresh = 0.6

for name, s in [("Linear", sim_pow1), ("Squared", sim_pow2), ("Cubed", sim_pow3)]:
    pots = s * amp
    firing = (pots >= thresh).sum()
    print(f"{name}: Max pot = {pots.max():.2f}, Mean pot = {pots.mean():.2f}, Firing = {firing} ({firing/N*100:.1f}%)")
