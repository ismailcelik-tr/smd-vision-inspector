"""Photo -> board registration: panel outline first, then fiducials.

photo ──panel quad──► coarse H (0° and 180° hypotheses)
      ──warp──► canonical ──ring search──► fiducials ──► final H
"""

from dataclasses import dataclass

import cv2
import numpy as np
from numpy.typing import NDArray

from smd_vision_inspector.recipe import BoardGeometry
from smd_vision_inspector.registration._homography import apply
from smd_vision_inspector.registration.fiducial import FiducialHit, locate_fiducial
from smd_vision_inspector.registration.frame import CanonicalFrame

__all__ = ["Registration", "RegistrationError", "panel_frame", "register", "warp_to_canonical"]

_CANONICAL_MM_PER_PX = 0.05
_SEARCH_MM = 2.5
_MIN_PANEL_AREA = 0.15
"""Panel share of the photo below which it is not trusted."""

_OUTLINE_BLUR_SIGMA = 2.0
_OUTLINE_CLOSE_PX = 15
_POLYGON_TOLERANCES = (0.01, 0.02, 0.04, 0.06)
"""approxPolyDP epsilon as a share of the outline perimeter."""

_QUAD_CORNERS = 4
_EDGE_MARGIN_PX = 2


class RegistrationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class Registration:
    homography: NDArray[np.float64]
    """Board mm -> photo px."""

    fiducial_scores: tuple[float, ...]


def panel_frame(geometry: BoardGeometry, mm_per_px: float = _CANONICAL_MM_PER_PX) -> CanonicalFrame:
    return CanonicalFrame(geometry.panel_origin_mm, geometry.panel_size_mm, mm_per_px)


def register(image: NDArray[np.uint8], geometry: BoardGeometry) -> Registration:
    gray = _gray(image)
    frame = panel_frame(geometry)
    quad = _find_panel(gray)

    best: tuple[NDArray[np.float64], tuple[float, ...]] | None = None
    for coarse in _hypotheses(quad, geometry):
        hits = _find_fiducials(gray, coarse, geometry, frame)
        if hits is None:
            continue

        scores = tuple(hit.score for hit in hits)
        if best is not None and min(scores) <= min(best[1]):
            continue

        canonical_px = np.array([hit.position_px for hit in hits])
        best = (apply(coarse @ np.linalg.inv(frame.matrix), canonical_px), scores)

    if best is None:
        raise RegistrationError("fiducials not found")

    photo_px, scores = best
    homography, _ = cv2.findHomography(np.array(geometry.fiducials_mm), photo_px)
    return Registration(homography.astype(np.float64), scores)


def warp_to_canonical(
    image: NDArray[np.uint8], registration: Registration, frame: CanonicalFrame
) -> NDArray[np.uint8]:
    return _warp(image, registration.homography, frame)


def _warp(
    image: NDArray[np.uint8], homography: NDArray[np.float64], frame: CanonicalFrame
) -> NDArray[np.uint8]:
    height, width = frame.shape
    photo_to_canonical = frame.matrix @ np.linalg.inv(homography)
    warped = cv2.warpPerspective(image, photo_to_canonical, (width, height), flags=cv2.INTER_LINEAR)
    return warped.astype(np.uint8, copy=False)


def _gray(image: NDArray[np.uint8]) -> NDArray[np.uint8]:
    if image.ndim == 2:
        return image

    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.uint8, copy=False)


def _find_panel(gray: NDArray[np.uint8]) -> NDArray[np.float64]:
    """Panel corners in photo px, clockwise."""
    blurred = cv2.GaussianBlur(gray, (0, 0), _OUTLINE_BLUR_SIGMA)
    _, mask = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((_OUTLINE_CLOSE_PX, _OUTLINE_CLOSE_PX), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise RegistrationError("panel not found")

    outline = max(contours, key=cv2.contourArea)
    if cv2.contourArea(outline) < _MIN_PANEL_AREA * gray.size:
        raise RegistrationError("panel not found")

    if _touches_edge(outline, gray.shape):
        raise RegistrationError("panel touches the photo edge")

    hull = cv2.convexHull(outline)
    perimeter = cv2.arcLength(hull, True)
    for tolerance in _POLYGON_TOLERANCES:
        polygon = cv2.approxPolyDP(hull, tolerance * perimeter, True)
        if len(polygon) == _QUAD_CORNERS:
            return _clockwise(polygon.reshape(_QUAD_CORNERS, 2).astype(np.float64))

    raise RegistrationError("panel outline is not a quadrilateral")


def _touches_edge(outline: cv2.typing.MatLike, shape: tuple[int, ...]) -> bool:
    x, y, width, height = cv2.boundingRect(outline)
    rows, cols = shape[:2]
    return (
        x <= _EDGE_MARGIN_PX
        or y <= _EDGE_MARGIN_PX
        or x + width >= cols - _EDGE_MARGIN_PX
        or y + height >= rows - _EDGE_MARGIN_PX
    )


def _clockwise(points: NDArray[np.float64]) -> NDArray[np.float64]:
    """Image rows grow downwards, so increasing angle runs clockwise on screen."""
    center = points.mean(axis=0)
    angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
    return points[np.argsort(angles)]


def _hypotheses(quad: NDArray[np.float64], geometry: BoardGeometry) -> list[NDArray[np.float64]]:
    """Board mm -> photo px for both ways the panel can lie (0° and 180°)."""
    x0, y0 = geometry.panel_origin_mm
    width, height = geometry.panel_size_mm
    # Clockwise as seen in the canonical image: TL, TR, BR, BL.
    corners_mm = np.array(
        [[x0, y0 + height], [x0 + width, y0 + height], [x0 + width, y0], [x0, y0]], np.float32
    )

    sides = np.linalg.norm(quad - np.roll(quad, -1, axis=0), axis=1)
    quad_long_first = sides[0] + sides[2] >= sides[1] + sides[3]
    start = 0 if quad_long_first == (width >= height) else 1

    return [
        cv2.getPerspectiveTransform(
            corners_mm, np.roll(quad, -s, axis=0).astype(np.float32)
        ).astype(np.float64)
        for s in (start, start + 2)
    ]


def _find_fiducials(
    gray: NDArray[np.uint8],
    coarse: NDArray[np.float64],
    geometry: BoardGeometry,
    frame: CanonicalFrame,
) -> list[FiducialHit] | None:
    canonical = _warp(gray, coarse, frame)
    search_px = round(_SEARCH_MM / frame.mm_per_px)
    ring_px = geometry.fiducial_ring_mm / frame.mm_per_px

    hits: list[FiducialHit] = []
    for expected in frame.to_px(np.array(geometry.fiducials_mm)):
        hit = locate_fiducial(canonical, expected, search_px, ring_px)
        if hit is None:
            return None
        hits.append(hit)

    return hits
