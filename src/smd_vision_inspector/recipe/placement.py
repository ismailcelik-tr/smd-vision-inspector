"""Component placement from the pick-and-place program."""

from dataclasses import dataclass

__all__ = ["Placement"]


@dataclass(frozen=True, slots=True)
class Placement:
    """Part center in board millimetres, origin at the lower-left corner."""

    refdes: str
    x_mm: float
    y_mm: float
    rotation_deg: float
    value: str
    footprint: str
