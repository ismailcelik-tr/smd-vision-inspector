"""Fiducial search: the dark ring around each fiducial pad."""

import math
from dataclasses import dataclass
from functools import cache

import cv2
import numpy as np
from numpy.typing import NDArray

__all__ = ["FiducialHit", "locate_fiducial"]

_MIN_SCORE = 0.5
_TEMPLATE_SPAN = 1.6
"""Template side relative to ring diameter."""

# Rings on one board vary in size and line width; search them all.
_DIAMETER_RATIOS = (0.8, 0.9, 1.0, 1.1, 1.2)
_WIDTH_RATIOS = (0.06, 0.15, 0.3)
"""Ring line width relative to its diameter."""

_SUBPIXEL_BITS = 4
_LIGHT = 255.0
_DARK = 0.0


@dataclass(frozen=True, slots=True)
class FiducialHit:
    position_px: tuple[float, float]
    score: float


def locate_fiducial(
    image: NDArray[np.uint8],
    expected_px: NDArray[np.float64],
    search_px: int,
    ring_px: float,
) -> FiducialHit | None:
    """Best ring match within ±search_px of expected_px, or None if too weak."""
    best: FiducialHit | None = None
    for template in _ring_templates(ring_px):
        hit = _match(image, expected_px, search_px, template)
        if hit is not None and (best is None or hit.score > best.score):
            best = hit

    if best is None or best.score < _MIN_SCORE:
        return None

    return best


def _match(
    image: NDArray[np.uint8],
    expected_px: NDArray[np.float64],
    search_px: int,
    template: NDArray[np.float32],
) -> FiducialHit | None:
    half = template.shape[0] // 2
    left = max(0, round(expected_px[0]) - search_px - half)
    top = max(0, round(expected_px[1]) - search_px - half)
    span = 2 * (search_px + half) + 1
    window = image[top : top + span, left : left + span].astype(np.float32)
    if window.shape[0] < template.shape[0] or window.shape[1] < template.shape[1]:
        return None

    scores = cv2.matchTemplate(window, template, cv2.TM_CCOEFF_NORMED).astype(
        np.float32, copy=False
    )
    _, best, _, (x, y) = cv2.minMaxLoc(scores)
    if not math.isfinite(best):
        return None

    dx, dy = _subpixel_offset(scores, x, y)
    return FiducialHit((left + x + dx + half, top + y + dy + half), best)


@cache
def _ring_templates(ring_px: float) -> tuple[NDArray[np.float32], ...]:
    return tuple(
        _ring_template(ring_px * diameter, width)
        for diameter in _DIAMETER_RATIOS
        for width in _WIDTH_RATIOS
    )


def _ring_template(ring_px: float, width_ratio: float) -> NDArray[np.float32]:
    size = 2 * math.ceil(ring_px * _TEMPLATE_SPAN / 2) + 1
    template = np.full((size, size), _LIGHT, np.float32)

    scale = 1 << _SUBPIXEL_BITS
    center = (size // 2) * scale
    thickness = max(1, round(ring_px * width_ratio))
    cv2.circle(
        template,
        (center, center),
        round(ring_px / 2 * scale),
        _DARK,
        thickness,
        cv2.LINE_AA,
        _SUBPIXEL_BITS,
    )
    return template


def _subpixel_offset(scores: NDArray[np.float32], x: int, y: int) -> tuple[float, float]:
    """Parabola through the peak and its neighbours, per axis."""
    height, width = scores.shape
    dx = _parabola_peak(*scores[y, x - 1 : x + 2]) if 0 < x < width - 1 else 0.0
    dy = _parabola_peak(*scores[y - 1 : y + 2, x]) if 0 < y < height - 1 else 0.0
    return dx, dy


def _parabola_peak(left: float, center: float, right: float) -> float:
    curvature = left - 2 * center + right
    if curvature >= 0:
        return 0.0

    return 0.5 * (left - right) / curvature
