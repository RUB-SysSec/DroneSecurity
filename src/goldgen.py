import numpy as np

def gold(Nc, l, seed):
    """Generate Gold sequence"""

    x1 = np.zeros(Nc + l + 31, dtype = bool)
    x2 = np.zeros(Nc + l + 31, dtype = bool)
    c = np.zeros(l, dtype = bool)

    for n in range(32):
        x2[n] = (seed >> n) & 1

    x1[0] = 1

    for n in range(Nc + l):
        x1[n + 31] = x1[n + 3] ^ x1[n]
        x2[n + 31] = x2[n + 3] ^ x2[n + 2] ^ x2[n+1] ^ x2[n]

    c = x1[Nc:Nc+l] ^ x2[Nc:Nc+l]

    return c
