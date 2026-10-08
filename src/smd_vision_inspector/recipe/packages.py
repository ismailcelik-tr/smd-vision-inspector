"""Package geometry and the CAD footprint names that map to it."""

from collections.abc import Mapping
from dataclasses import dataclass

__all__ = ["Package", "PackageLibrary"]

_SQUARE_TOLERANCE_MM = 0.05


@dataclass(frozen=True, slots=True)
class Package:
    name: str
    size_mm: tuple[float, float]
    """Envelope including leads at 0° rotation: (along x, along y)."""

    polar: bool = False
    """Body itself is asymmetric, whatever the part kind."""

    bom_tokens: tuple[str, ...] = ()
    """Words that name this package in BOM descriptions."""

    @property
    def is_square(self) -> bool:
        width, height = self.size_mm
        return abs(width - height) <= _SQUARE_TOLERANCE_MM


@dataclass(frozen=True, slots=True)
class PackageLibrary:
    packages: Mapping[str, Package]
    footprints: Mapping[str, str]
    """CAD footprint name -> package name."""
