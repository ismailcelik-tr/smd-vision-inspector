"""Samsung/Hanwha SM-series placement program (.ssa) reader."""

import shlex
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from smd_vision_inspector.recipe.placement import Placement

__all__ = ["SsaProgram", "merge_placements", "parse_ssa", "read_ssa"]

_ENCODING = "cp1254"
_PLACEMENTS_SECTION = "[PLACEMENTS]"
_MILLIMETER = "MILIMETER"  # sic, as written by the machine software
_LOWER_LEFT = "LOWER LEFT"
_NOT_SKIPPED = "0"

# Placement line columns; the ones in between are not used.
_REFDES, _X, _Y, _ROTATION, _SKIP, _VALUE, _FOOTPRINT = 0, 1, 2, 4, 11, 12, 14
_FIELD_COUNT = 15


@dataclass(frozen=True, slots=True)
class SsaProgram:
    board_name: str
    size_mm: tuple[float, float]
    placements: tuple[Placement, ...]
    skipped: frozenset[str]
    """Parts this machine skips; another machine places them."""


def read_ssa(path: Path) -> SsaProgram:
    return parse_ssa(path.read_text(encoding=_ENCODING))


def parse_ssa(text: str) -> SsaProgram:
    header: dict[str, str] = {}
    placements: list[Placement] = []
    skipped: set[str] = set()
    in_placements = False

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue

        if line.startswith("["):
            in_placements = line == _PLACEMENTS_SECTION
            continue

        if not in_placements:
            key, _, value = line.partition("=")
            header[key.strip()] = value.strip()
            continue

        placement, is_skipped = _parse_placement(line)
        if is_skipped:
            skipped.add(placement.refdes)
            continue

        placements.append(placement)

    _require(header, "Unit System", _MILLIMETER, "unit system")
    _require(header, "Coordinate", _LOWER_LEFT, "coordinate origin")
    width, height = (float(v) for v in header["PCB Size"].split(",")[:2])

    return SsaProgram(
        board_name=header["Board Name"],
        size_mm=(width, height),
        placements=tuple(placements),
        skipped=frozenset(skipped),
    )


def merge_placements(programs: Iterable[SsaProgram]) -> tuple[Placement, ...]:
    """Combine programs of machines that share one board."""
    merged: dict[str, Placement] = {}
    for program in programs:
        for placement in program.placements:
            if placement.refdes in merged:
                raise ValueError(f"{placement.refdes} placed by more than one program")
            merged[placement.refdes] = placement

    return tuple(merged.values())


def _parse_placement(line: str) -> tuple[Placement, bool]:
    fields = shlex.split(line)
    if len(fields) < _FIELD_COUNT:
        raise ValueError(f"truncated placement line: {line}")

    placement = Placement(
        refdes=fields[_REFDES],
        x_mm=float(fields[_X]),
        y_mm=float(fields[_Y]),
        rotation_deg=float(fields[_ROTATION]),
        value=fields[_VALUE],
        footprint=fields[_FOOTPRINT],
    )
    return placement, fields[_SKIP] != _NOT_SKIPPED


def _require(header: dict[str, str], key: str, expected: str, what: str) -> None:
    actual = header.get(key)
    if actual != expected:
        raise ValueError(f"unsupported {what}: {actual!r}")
