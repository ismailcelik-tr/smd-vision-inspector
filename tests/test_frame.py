import numpy as np

from smd_vision_inspector.registration import CanonicalFrame

FRAME = CanonicalFrame(origin_mm=(-5.0, -5.0), size_mm=(20.0, 10.0), mm_per_px=0.5)


def test_board_y_up_maps_to_image_y_down() -> None:
    corners = FRAME.to_px(np.array([[-5.0, 5.0], [15.0, -5.0]]))

    np.testing.assert_allclose(corners, [[0.0, 0.0], [40.0, 20.0]])


def test_shape_covers_extent() -> None:
    assert FRAME.shape == (20, 40)


def test_from_px_inverts_to_px() -> None:
    points = np.array([[1.25, 2.5], [-3.0, 4.0]])

    np.testing.assert_allclose(FRAME.from_px(FRAME.to_px(points)), points)
