import numpy as np

EPS = 1e-8

def rho_energy(C: np.ndarray, A: np.ndarray) -> float:
    # absorbed "energy" proxy (norm loss)
    return float((np.linalg.norm(C) - np.linalg.norm(A)) / (np.linalg.norm(C) + EPS))

def softmax(x: np.ndarray) -> np.ndarray:
    x = x - np.max(x)  # stability
    ex = np.exp(x)
    return ex / (np.sum(ex) + 1e-12)

def entropy(p: np.ndarray) -> float:
    p = np.clip(p, 1e-12, 1.0)
    return float(-np.sum(p * np.log(p)))

def max_weight(p: np.ndarray) -> float:
    return float(np.max(p)) if p.size else 0.0

def l2(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))

