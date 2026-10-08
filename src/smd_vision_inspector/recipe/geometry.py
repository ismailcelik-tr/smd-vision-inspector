"""Physical board layout used to register photos."""

from dataclasses import dataclass

__all__ = ["BoardGeometry"]


@dataclass(frozen=True, slots=True)
class BoardGeometry:
    """Board millimetres, origin at the lower-left corner of the board (rails excluded)."""

    panel_origin_mm: tuple[float, float]
    """Lower-left corner of the panel outline, rails included."""

    panel_size_mm: tuple[float, float]
    fiducials_mm: tuple[tuple[float, float], ...]
    fiducial_ring_mm: float
    """Diameter of the dark ring every fiducial shows."""
