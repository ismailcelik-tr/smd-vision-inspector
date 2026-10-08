"""Point mapping through 3x3 homogeneous transforms."""

import numpy as np
from numpy.typing import NDArray

__all__ = ["apply"]


def apply(matrix: NDArray[np.float64], points: NDArray[np.float64]) -> NDArray[np.float64]:
    mapped = np.column_stack([points, np.ones(len(points))]) @ matrix.T
    return mapped[:, :2] / mapped[:, 2:]
