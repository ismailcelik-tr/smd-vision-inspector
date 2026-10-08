from dataclasses import replace

import cv2
import numpy as np
import pytest

from smd_vision_inspector.registration import (
    RegistrationError,
    locate_fiducial,
    panel_frame,
    register,
    warp_to_canonical,
)

from .synthetic import GEOMETRY, Matrix, photograph, project, render_truth

TILTED = [(250.0, 300.0), (2150.0, 220.0), (2230.0, 1450.0), (180.0, 1560.0)]
UPSIDE_DOWN = TILTED[2:] + TILTED[:2]
MAX_ERROR_MM = 0.1
"""Worst case at the board corner farthest from the fiducials; ECC refinement comes later."""

BOARD_SIZE_MM = (151.0, 87.706)


def _check_points() -> np.ndarray:
    width, height = BOARD_SIZE_MM
    corners = [[0.0, 0.0], [width, 0.0], [width, height], [0.0, height]]
    return np.array([*GEOMETRY.fiducials_mm, *corners, [width / 2, height / 2]])


def _max_error_mm(estimated: Matrix, truth: Matrix) -> float:
    """Where the estimate sends each true photo point, back on the board."""
    points = _check_points()
    recovered = project(np.linalg.inv(estimated), project(truth, points))
    return float(np.linalg.norm(recovered - points, axis=1).max())


@pytest.mark.parametrize("corners", [TILTED, UPSIDE_DOWN], ids=["tilted", "upside_down"])
def test_recovers_board_to_photo_homography(corners: list[tuple[float, float]]) -> None:
    photo, truth = photograph(*render_truth(), corners)

    registration = register(photo, GEOMETRY)

    assert _max_error_mm(registration.homography, truth) < MAX_ERROR_MM


def test_accepts_color_photo() -> None:
    photo, truth = photograph(*render_truth(), TILTED)

    color = cv2.cvtColor(photo, cv2.COLOR_GRAY2BGR).astype(np.uint8, copy=False)

    registration = register(color, GEOMETRY)

    assert _max_error_mm(registration.homography, truth) < MAX_ERROR_MM


def test_rejects_photo_without_panel() -> None:
    with pytest.raises(RegistrationError, match="panel"):
        register(np.full((1200, 1600), 35, np.uint8), GEOMETRY)


def test_rejects_panel_cut_by_photo_edge() -> None:
    shifted = [(x - 400.0, y) for x, y in TILTED]
    photo, _ = photograph(*render_truth(), shifted)

    with pytest.raises(RegistrationError, match="edge"):
        register(photo, GEOMETRY)


def test_rejects_panel_without_fiducials() -> None:
    truth, frame = render_truth(replace(GEOMETRY, fiducials_mm=()))
    photo, _ = photograph(truth, frame, TILTED)

    with pytest.raises(RegistrationError, match="fiducial"):
        register(photo, GEOMETRY)


def test_warp_puts_fiducials_where_the_frame_expects_them() -> None:
    photo, _ = photograph(*render_truth(), TILTED)
    frame = panel_frame(GEOMETRY, mm_per_px=0.05)

    canonical = warp_to_canonical(photo, register(photo, GEOMETRY), frame)

    assert canonical.shape == frame.shape
    ring_px = GEOMETRY.fiducial_ring_mm / frame.mm_per_px
    for expected in frame.to_px(np.array(GEOMETRY.fiducials_mm)):
        hit = locate_fiducial(canonical, expected, 20, ring_px)
        assert hit is not None
        assert np.linalg.norm(np.array(hit.position_px) - expected) < 0.5
