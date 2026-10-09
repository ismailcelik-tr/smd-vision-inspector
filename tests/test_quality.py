import cv2
import numpy as np
import pytest

from smd_vision_inspector.quality import Reason, assess
from smd_vision_inspector.registration import Registration, register

from .synthetic import GEOMETRY, Image, photograph, render_truth

SIZE = (4000, 2800)
SQUARE_ON = [(250.0, 300.0), (3750.0, 260.0), (3790.0, 2450.0), (210.0, 2480.0)]
"""Panel ≈ 0.046 mm/px, almost no perspective."""

SMALL = [(250.0, 300.0), (2150.0, 220.0), (2230.0, 1450.0), (180.0, 1560.0)]
MILD_KEYSTONE = [(400.0, 300.0), (3600.0, 300.0), (3790.0, 2480.0), (210.0, 2480.0)]
"""≈7° tilt at 20 cm."""

KEYSTONE = [(900.0, 300.0), (3100.0, 300.0), (3790.0, 2480.0), (210.0, 2480.0)]
BLUR_SIGMA_PX = 4.0
GLARE_RADIUS_PX = 220
SATURATED = 255
SPECK_RADIUS_PX = 3
SPECK_PITCH_PX = 20


def _shot(corners: list[tuple[float, float]]) -> tuple[Image, Registration]:
    photo, _ = photograph(*render_truth(), corners, size=SIZE)
    return photo, register(photo, GEOMETRY)


@pytest.fixture(scope="module")
def square_on() -> tuple[Image, Registration]:
    return _shot(SQUARE_ON)


def test_accepts_sharp_square_on_photo(square_on: tuple[Image, Registration]) -> None:
    report = assess(*square_on, GEOMETRY)

    assert report.reasons == ()
    assert report.ok


def test_reports_resolution(square_on: tuple[Image, Registration]) -> None:
    report = assess(*square_on, GEOMETRY)

    assert report.mm_per_px == pytest.approx(0.046, abs=0.002)


def test_flags_low_resolution() -> None:
    report = assess(*_shot(SMALL), GEOMETRY)

    assert Reason.LOW_RESOLUTION in report.reasons
    assert not report.ok


def test_accepts_mild_perspective() -> None:
    report = assess(*_shot(MILD_KEYSTONE), GEOMETRY)

    assert report.reasons == ()


def test_flags_strong_perspective() -> None:
    report = assess(*_shot(KEYSTONE), GEOMETRY)

    assert Reason.TILTED in report.reasons


def test_flags_blur(square_on: tuple[Image, Registration]) -> None:
    photo, registration = square_on
    blurred = cv2.GaussianBlur(photo, (0, 0), BLUR_SIGMA_PX).astype(np.uint8, copy=False)

    report = assess(blurred, registration, GEOMETRY)

    assert report.reasons == (Reason.BLURRY,)


def test_flags_glare(square_on: tuple[Image, Registration]) -> None:
    photo, registration = square_on
    glared = photo.copy()
    center = (SIZE[0] // 2, SIZE[1] // 2)
    cv2.circle(glared, center, GLARE_RADIUS_PX, SATURATED, -1)

    report = assess(glared, registration, GEOMETRY)

    assert report.reasons == (Reason.GLARE,)


def test_ignores_small_saturated_specks(square_on: tuple[Image, Registration]) -> None:
    """White silkscreen saturates too, but only in thin strokes."""
    photo, registration = square_on
    specked = photo.copy()
    for y in range(400, 2400, SPECK_PITCH_PX):
        for x in range(400, 3600, SPECK_PITCH_PX):
            cv2.circle(specked, (x, y), SPECK_RADIUS_PX, SATURATED, -1)

    report = assess(specked, registration, GEOMETRY)

    assert report.reasons == ()
