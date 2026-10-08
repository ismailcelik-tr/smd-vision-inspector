"""Synthetic panels and photos with known geometry."""

import cv2
import numpy as np
from numpy.typing import NDArray

from smd_vision_inspector.recipe import BoardGeometry
from smd_vision_inspector.registration import CanonicalFrame

Image = NDArray[np.uint8]
Matrix = NDArray[np.float64]

GEOMETRY = BoardGeometry(
    panel_origin_mm=(-5.0, -5.0),
    panel_size_mm=(161.0, 97.9),
    fiducials_mm=((3.9, 85.8), (114.0, 77.1), (31.537, 65.589), (98.219, 3.72)),
    fiducial_ring_mm=1.7,
)

TRUTH_MM_PER_PX = 0.025

_MASK = 215
_PAD = 175
_RING = 70
_PART = 45
_HOLE = 10
_RING_WIDTH_MM = 0.15
_PAD_MM = 3.0
_SUBPIXEL_BITS = 4

# (x, y, width, height) in board mm
_PARTS = (
    (44.9, 56.9, 9.0, 9.0),
    (94.5, 52.8, 9.0, 9.0),
    (136.1, 28.9, 10.3, 17.9),
    (20.0, 20.0, 3.2, 1.6),
)
_HOLE_MM = ((14.7, 66.5, 3.2), (147.6, 1.9, 3.2))


def render_truth(
    geometry: BoardGeometry = GEOMETRY, ring_width_mm: float = _RING_WIDTH_MM
) -> tuple[Image, CanonicalFrame]:
    frame = CanonicalFrame(geometry.panel_origin_mm, geometry.panel_size_mm, TRUTH_MM_PER_PX)
    image = np.full(frame.shape, _MASK, np.uint8)

    for x, y, w, h in _PARTS:
        corners = frame.to_px(np.array([[x - w / 2, y + h / 2], [x + w / 2, y - h / 2]]))
        cv2.rectangle(image, _point(corners[0]), _point(corners[1]), _PART, -1)

    for x, y, diameter in _HOLE_MM:
        _disk(image, frame, (x, y), diameter, _HOLE)

    for center in geometry.fiducials_mm:
        _disk(image, frame, center, _PAD_MM, _PAD)
        radius = geometry.fiducial_ring_mm / 2 / TRUTH_MM_PER_PX
        thickness = max(1, round(ring_width_mm / TRUTH_MM_PER_PX))
        _circle(image, frame.to_px(np.array([center]))[0], radius, _RING, thickness)

    return image, frame


def photograph(
    truth: Image,
    frame: CanonicalFrame,
    panel_corners_px: list[tuple[float, float]],
    size: tuple[int, int] = (2400, 1800),
    background: int = 35,
    noise: float = 2.0,
    seed: int = 0,
) -> tuple[Image, Matrix]:
    """Corners in photo px for the panel's top-left, top-right, bottom-right, bottom-left.

    Returns the photo and the true board-mm -> photo-px homography.
    """
    x0, y0 = frame.origin_mm
    width, height = frame.size_mm
    corners_mm = np.array(
        [[x0, y0 + height], [x0 + width, y0 + height], [x0 + width, y0], [x0, y0]], np.float32
    )
    homography = cv2.getPerspectiveTransform(
        corners_mm, np.array(panel_corners_px, np.float32)
    ).astype(np.float64)

    smooth = cv2.GaussianBlur(truth, (0, 0), 1.2)
    photo = cv2.warpPerspective(
        smooth,
        homography @ np.linalg.inv(frame.matrix),
        size,
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=background,
    )

    rng = np.random.default_rng(seed)
    noisy = photo.astype(np.float64) + rng.normal(0.0, noise, photo.shape)
    return np.clip(noisy, 0, 255).astype(np.uint8), homography


def project(homography: Matrix, points_mm: NDArray[np.float64]) -> NDArray[np.float64]:
    homogeneous = np.column_stack([points_mm, np.ones(len(points_mm))]) @ homography.T
    return homogeneous[:, :2] / homogeneous[:, 2:]


def _disk(
    image: Image, frame: CanonicalFrame, center: tuple[float, float], diameter: float, value: int
) -> None:
    _circle(image, frame.to_px(np.array([center]))[0], diameter / 2 / frame.mm_per_px, value, -1)


def _circle(
    image: Image, center_px: NDArray[np.float64], radius_px: float, value: int, thickness: int
) -> None:
    """Sub-pixel accurate circle."""
    scale = 1 << _SUBPIXEL_BITS
    center = (round(center_px[0] * scale), round(center_px[1] * scale))
    cv2.circle(
        image, center, round(radius_px * scale), value, thickness, cv2.LINE_AA, _SUBPIXEL_BITS
    )


def _point(px: NDArray[np.float64]) -> tuple[int, int]:
    return round(px[0]), round(px[1])
