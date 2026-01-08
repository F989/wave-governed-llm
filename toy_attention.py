import numpy as np
from wave_metrics import softmax

def governed_attention(query: np.ndarray,
                       keys: np.ndarray,
                       values: np.ndarray,
                       damping: float):
    """
    toy attention:
      scores_i = <q, k_i> / (1 + damping)
      weights = softmax(scores)
      output = Σ w_i * v_i
    """
    scores = np.array([np.dot(query, k) for k in keys], dtype=float)
    scores /= (1.0 + float(damping))
    weights = softmax(scores)
    output = np.sum(weights[:, None] * values, axis=0)
    return output, weights, scores

