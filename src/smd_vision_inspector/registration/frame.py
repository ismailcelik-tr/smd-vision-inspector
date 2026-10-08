"""Canonical image frame: fixed resolution, board millimetres to pixels."""

import math
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from smd_vision_inspector.registration._homography import apply

__all__ = ["CanonicalFrame"]


@dataclass(frozen=True, slots=True)
class CanonicalFrame:
    """Board coordinates are y-up; image rows grow downwards."""

    origin_mm: tuple[float, float]
    """Lower-left corner of the covered area."""

    size_mm: tuple[float, float]
    mm_per_px: float

    @property
    def shape(self) -> tuple[int, int]:
        width, height = self.size_mm
        return math.ceil(height / self.mm_per_px), math.ceil(width / self.mm_per_px)

    @property
    def matrix(self) -> NDArray[np.float64]:
        """Homogeneous board-mm -> canonical-px transform."""
        x0, y0 = self.origin_mm
        top = y0 + self.size_mm[1]
        scale = 1.0 / self.mm_per_px
        return np.array(
            [
                [scale, 0.0, -x0 * scale],
                [0.0, -scale, top * scale],
                [0.0, 0.0, 1.0],
            ]
        )

    def to_px(self, points_mm: NDArray[np.float64]) -> NDArray[np.float64]:
        return apply(self.matrix, points_mm)

    def from_px(self, points_px: NDArray[np.float64]) -> NDArray[np.float64]:
        return apply(np.linalg.inv(self.matrix), points_px)
