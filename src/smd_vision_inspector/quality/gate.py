from dataclasses import dataclass
from enum import StrEnum

import cv2
import numpy as np
from numpy.typing import NDArray

from smd_vision_inspector.recipe import BoardGeometry
from smd_vision_inspector.registration import Registration, panel_frame, warp_to_canonical

__all__ = ["QualityLimits", "QualityReport", "Reason", "assess"]

_SATURATED = 250
_GLARE_OPEN_MM = 0.45
"""Opening removes thin saturated strokes (white silkscreen, pin tips)."""

_DENOISE_SIGMA_PX = 0.7
_SOBEL_GAIN = 8.0
_EDGE_PERCENTILE = 99.5
_EDGE_SHARE = 0.3
"""Edge pixels: gradient above this share of the strongest gradients."""

_EDGE_BAND_PX = 7


class Reason(StrEnum):
    LOW_RESOLUTION = "low_resolution"
    TILTED = "tilted"
    BLURRY = "blurry"
    GLARE = "glare"


@dataclass(frozen=True, slots=True)
class QualityLimits:
    max_mm_per_px: float = 0.07
    max_scale_ratio: float = 1.3
    """Largest over smallest panel-corner scale; ≈7-11° tilt at 14-20 cm."""

    min_sharpness: float = 2.2
    """Golden iPhone photos: 3.0-3.4; 0.05 mm extra blur: ≈2.5."""

    max_glare_mm2: float = 5.0
    """Golden iPhone photos: ≤ 1 mm²."""


@dataclass(frozen=True, slots=True)
class QualityReport:
    reasons: tuple[Reason, ...]
    mm_per_px: float
    """Worst direction, worst panel corner."""

    scale_ratio: float
    sharpness: float
    glare_mm2: float
    """Largest saturated spot."""

    @property
    def ok(self) -> bool:
        return not self.reasons


_DEFAULT_LIMITS = QualityLimits()


def assess(
    image: NDArray[np.uint8],
    registration: Registration,
    geometry: BoardGeometry,
    limits: QualityLimits = _DEFAULT_LIMITS,
) -> QualityReport:
    jacobians = [_jacobian(registration.homography, corner) for corner in _corners(geometry)]
    mm_per_px = max(1.0 / np.linalg.svd(j, compute_uv=False)[-1] for j in jacobians)
    scales = [np.sqrt(abs(np.linalg.det(j))) for j in jacobians]
    scale_ratio = max(scales) / min(scales)

    frame = panel_frame(geometry)
    canonical = _gray(warp_to_canonical(image, registration, frame))
    sharpness = _sharpness(canonical)
    glare_mm2 = _largest_glare_mm2(canonical, frame.mm_per_px)

    checks = (
        (Reason.LOW_RESOLUTION, mm_per_px > limits.max_mm_per_px),
        (Reason.TILTED, scale_ratio > limits.max_scale_ratio),
        (Reason.BLURRY, sharpness < limits.min_sharpness),
        (Reason.GLARE, glare_mm2 > limits.max_glare_mm2),
    )
    reasons = tuple(reason for reason, failed in checks if failed)
    return QualityReport(reasons, float(mm_per_px), float(scale_ratio), sharpness, glare_mm2)


def _corners(geometry: BoardGeometry) -> list[tuple[float, float]]:
    x0, y0 = geometry.panel_origin_mm
    width, height = geometry.panel_size_mm
    return [(x0, y0), (x0 + width, y0), (x0 + width, y0 + height), (x0, y0 + height)]


def _jacobian(homography: NDArray[np.float64], point: tuple[float, float]) -> NDArray[np.float64]:
    """d(photo px) / d(board mm) at point."""
    xyw = homography @ np.array([*point, 1.0])
    w = float(xyw[2])
    jacobian = (homography[:2, :2] * w - np.outer(xyw[:2], homography[2, :2])) / w**2
    return jacobian.astype(np.float64, copy=False)


def _sharpness(gray: NDArray[np.uint8]) -> float:
    """Σ|Laplacian| / Σ|gradient| along strong edges.

    Scales with 1 / edge width; contrast and edge count cancel out.
    """
    smooth = cv2.GaussianBlur(gray.astype(np.float32), (0, 0), _DENOISE_SIGMA_PX)
    laplacian = np.abs(cv2.Laplacian(smooth, cv2.CV_32F, ksize=3))
    dx = cv2.Sobel(smooth, cv2.CV_32F, 1, 0, ksize=3)
    dy = cv2.Sobel(smooth, cv2.CV_32F, 0, 1, ksize=3)
    gradient = np.hypot(dx, dy) / _SOBEL_GAIN

    strong = gradient > _EDGE_SHARE * np.percentile(gradient, _EDGE_PERCENTILE)
    band = cv2.dilate(strong.astype(np.uint8), np.ones((_EDGE_BAND_PX, _EDGE_BAND_PX), np.uint8))
    near_edges = band.astype(bool)
    return float(laplacian[near_edges].sum() / gradient[near_edges].sum())


def _largest_glare_mm2(gray: NDArray[np.uint8], mm_per_px: float) -> float:
    open_px = round(_GLARE_OPEN_MM / mm_per_px)
    saturated = (gray >= _SATURATED).astype(np.uint8)
    spots = cv2.morphologyEx(saturated, cv2.MORPH_OPEN, np.ones((open_px, open_px), np.uint8))
    count, _, stats, _ = cv2.connectedComponentsWithStats(spots)
    if count < 2:
        return 0.0

    return float(stats[1:, cv2.CC_STAT_AREA].max()) * mm_per_px**2


def _gray(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    if image.ndim == 2:
        return image

    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.uint8, copy=False)
