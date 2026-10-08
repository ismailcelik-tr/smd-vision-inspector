from dataclasses import replace

import cv2
import numpy as np
import pytest

from smd_vision_inspector.registration import CanonicalFrame, locate_fiducial

from .synthetic import GEOMETRY, render_truth

MM_PER_PX = 0.05
RING_PX = GEOMETRY.fiducial_ring_mm / MM_PER_PX
SEARCH_PX = 50


def _canonical(
    shift: tuple[float, float],
    ring_mm: float = GEOMETRY.fiducial_ring_mm,
    ring_width_mm: float = 0.15,
) -> tuple[np.ndarray, CanonicalFrame]:
    truth, truth_frame = render_truth(replace(GEOMETRY, fiducial_ring_mm=ring_mm), ring_width_mm)
    frame = CanonicalFrame(truth_frame.origin_mm, truth_frame.size_mm, MM_PER_PX)
    scale = truth_frame.mm_per_px / MM_PER_PX
    matrix = np.array([[scale, 0, shift[0]], [0, scale, shift[1]]])
    height, width = frame.shape
    smooth = cv2.GaussianBlur(truth, (0, 0), 1.0)
    canonical = cv2.warpAffine(smooth, matrix, (width, height), flags=cv2.INTER_AREA)
    return canonical.astype(np.uint8, copy=False), frame


def test_finds_ring_center_with_subpixel_accuracy() -> None:
    shift = (0.3, -0.4)
    image, frame = _canonical(shift)
    expected = frame.to_px(np.array([GEOMETRY.fiducials_mm[2]]))[0] + shift

    hit = locate_fiducial(image, expected + np.array([6.0, -4.0]), SEARCH_PX, RING_PX)

    assert hit is not None
    assert np.linalg.norm(np.array(hit.position_px) - expected) < 0.2


def test_misses_when_no_ring_in_window() -> None:
    image, frame = _canonical((0.0, 0.0))
    empty_spot = frame.to_px(np.array([[75.0, 30.0]]))[0]

    assert locate_fiducial(image, empty_spot, SEARCH_PX, RING_PX) is None


@pytest.mark.parametrize(("diameter_ratio", "width_mm"), [(1.2, 0.5), (1.2, 0.1), (0.85, 0.5)])
def test_finds_rings_that_differ_from_nominal(diameter_ratio: float, width_mm: float) -> None:
    # Fiducials on one board differ: 0.1-0.55 mm ring width, ±20 % diameter.
    shift = (0.2, 0.1)
    ring_mm = GEOMETRY.fiducial_ring_mm * diameter_ratio
    image, frame = _canonical(shift, ring_mm=ring_mm, ring_width_mm=width_mm)
    expected = frame.to_px(np.array([GEOMETRY.fiducials_mm[0]]))[0] + shift

    hit = locate_fiducial(image, expected, SEARCH_PX, RING_PX)

    assert hit is not None
    assert np.linalg.norm(np.array(hit.position_px) - expected) < 0.2
