"""Bill of materials reader for the company xlsx BOM form."""

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

import openpyxl

from smd_vision_inspector.recipe.placement import Placement

__all__ = ["BomLine", "Reconciliation", "parse_bom_rows", "read_bom", "reconcile"]

_HEADER = ("Stok No", "Stok Adı", "Miktar", "Konum")
_REFDES_SEPARATOR = ","


@dataclass(frozen=True, slots=True)
class BomLine:
    stock_code: str
    description: str
    quantity: int
    refdes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Reconciliation:
    unplaced: tuple[str, ...]
    """In the BOM, placed by no program: through-hole, DNP or another variant."""

    unlisted: tuple[str, ...]
    """Placed, absent from the BOM."""

    quantity_mismatches: tuple[BomLine, ...]


def read_bom(path: Path) -> tuple[BomLine, ...]:
    """Read the single sheet that holds BOM lines; template sheets are ignored."""
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        parsed = [parse_bom_rows(sheet.iter_rows(values_only=True)) for sheet in workbook]
    finally:
        workbook.close()

    found = [lines for lines in parsed if lines]
    if len(found) != 1:
        raise ValueError(f"expected one BOM sheet, found {len(found)} sheets with lines")

    return found[0]


def parse_bom_rows(rows: Iterable[Sequence[object]]) -> tuple[BomLine, ...]:
    lines: list[BomLine] = []
    in_body = False

    for row in rows:
        cells = tuple(row[: len(_HEADER)])
        if not in_body:
            in_body = cells == _HEADER
            continue

        line = _parse_line(cells)
        if line is not None:
            lines.append(line)

    return tuple(lines)


def reconcile(placements: Iterable[Placement], lines: Iterable[BomLine]) -> Reconciliation:
    lines = tuple(lines)
    placed = {p.refdes for p in placements}
    listed = {refdes for line in lines for refdes in line.refdes}

    return Reconciliation(
        unplaced=_natural_sorted(listed - placed),
        unlisted=_natural_sorted(placed - listed),
        quantity_mismatches=tuple(line for line in lines if line.quantity != len(line.refdes)),
    )


def _parse_line(cells: tuple[object, ...]) -> BomLine | None:
    if len(cells) < len(_HEADER):
        return None

    stock_code, description, quantity, location = cells
    if not isinstance(quantity, int) or not isinstance(location, str):
        return None

    refdes = tuple(r.strip() for r in location.split(_REFDES_SEPARATOR) if r.strip())
    if not refdes:
        return None

    return BomLine(str(stock_code), str(description).strip(), quantity, refdes)


def _natural_sorted(refdes: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(refdes, key=_natural_key))


def _natural_key(refdes: str) -> list[int | str]:
    """R2 before R10."""
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", refdes)]
