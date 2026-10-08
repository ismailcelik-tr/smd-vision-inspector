"""Per-part inspection targets built from placements, BOM and package library."""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from smd_vision_inspector.recipe.bom import BomLine
from smd_vision_inspector.recipe.packages import Package, PackageLibrary
from smd_vision_inspector.recipe.parts import PartKind, kind_of
from smd_vision_inspector.recipe.placement import Placement

__all__ = ["InspectionTarget", "OrientationCheck", "build_targets"]

_POLAR_KINDS = frozenset({PartKind.DIODE, PartKind.LED, PartKind.TRANSISTOR, PartKind.IC})


class OrientationCheck(StrEnum):
    NONE = "none"
    HALF_TURN = "half_turn"
    """Distinguish 0° from 180°."""

    QUARTER_TURN = "quarter_turn"
    """Square body: any of the four orientations."""


@dataclass(frozen=True, slots=True)
class InspectionTarget:
    refdes: str
    kind: PartKind
    package: str
    center_mm: tuple[float, float]
    rotation_deg: float
    size_mm: tuple[float, float]
    orientation: OrientationCheck


def build_targets(
    placements: Iterable[Placement],
    bom_lines: Iterable[BomLine],
    library: PackageLibrary,
    package_overrides: Mapping[str, str] | None = None,
    orientation_overrides: Mapping[str, OrientationCheck] | None = None,
) -> tuple[InspectionTarget, ...]:
    """Package priority: override, then CAD footprint, then BOM description."""
    overrides = package_overrides or {}
    orientations = orientation_overrides or {}
    descriptions = {refdes: line.description for line in bom_lines for refdes in line.refdes}
    targets: list[InspectionTarget] = []
    unresolved: list[str] = []

    for placement in placements:
        refdes = placement.refdes
        package = _resolve(placement, descriptions.get(refdes, ""), library, overrides)
        if package is None:
            unresolved.append(refdes)
            continue

        kind = kind_of(refdes)
        targets.append(
            InspectionTarget(
                refdes=refdes,
                kind=kind,
                package=package.name,
                center_mm=(placement.x_mm, placement.y_mm),
                rotation_deg=placement.rotation_deg,
                size_mm=package.size_mm,
                orientation=orientations.get(refdes, _orientation(kind, package)),
            )
        )

    if unresolved:
        raise ValueError(f"no package for: {', '.join(unresolved)}")

    return tuple(targets)


def _resolve(
    placement: Placement,
    description: str,
    library: PackageLibrary,
    overrides: Mapping[str, str],
) -> Package | None:
    name = overrides.get(placement.refdes) or library.footprints.get(placement.footprint)
    if name is not None:
        return library.packages.get(name)

    words = set(re.split(r"[\s,]+", description))
    for package in library.packages.values():
        if words.intersection(package.bom_tokens):
            return package

    return None


def _orientation(kind: PartKind, package: Package) -> OrientationCheck:
    if kind not in _POLAR_KINDS and not package.polar:
        return OrientationCheck.NONE

    if package.is_square:
        return OrientationCheck.QUARTER_TURN

    return OrientationCheck.HALF_TURN
