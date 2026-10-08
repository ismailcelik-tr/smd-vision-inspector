from pathlib import Path

import openpyxl
import pytest

from smd_vision_inspector.recipe import (
    BomLine,
    Placement,
    parse_bom_rows,
    read_bom,
    reconcile,
)

TITLE = (None, "BOM LİSTESİ", "Doküman No:", "F450")
HEADER = ("Stok No", "Stok Adı", "Miktar", "Konum")
R40 = ("H.E.DIR.00095", "DIRENC 8K2 %1 1206 1/4W", 1, "R40")
R63_R83 = ("H.E.DIR.00103", "DIRENC 5K1 %1 1206 1/4W", 2, "R63, R83")
PCB = ("H.E.PCB.62601", "PCB, DEMO R01", 1, None)
FOOTER = ("HAZIRLAYAN", "KONTROL EDEN", "ONAYLAYAN", None)


def _placement(refdes: str) -> Placement:
    return Placement(refdes, 0.0, 0.0, 0.0, "", "")


def _line(refdes: tuple[str, ...], quantity: int) -> BomLine:
    return BomLine("H.E.X", "PART", quantity, refdes)


def test_parses_lines_after_header() -> None:
    lines = parse_bom_rows([TITLE, HEADER, R40, R63_R83])

    assert lines == (
        BomLine("H.E.DIR.00095", "DIRENC 8K2 %1 1206 1/4W", 1, ("R40",)),
        BomLine("H.E.DIR.00103", "DIRENC 5K1 %1 1206 1/4W", 2, ("R63", "R83")),
    )


def test_skips_rows_without_refdes() -> None:
    lines = parse_bom_rows([HEADER, R40, PCB, FOOTER])

    assert [line.stock_code for line in lines] == ["H.E.DIR.00095"]


def test_returns_nothing_without_header() -> None:
    assert parse_bom_rows([TITLE, R40]) == ()


def _write_workbook(path: Path, sheets: dict[str, list[tuple[object, ...]]]) -> None:
    workbook = openpyxl.Workbook()
    workbook.remove(workbook.active)  # type: ignore[arg-type]
    for title, rows in sheets.items():
        sheet = workbook.create_sheet(title)
        for row in rows:
            sheet.append(row)
    workbook.save(path)


def test_reads_sheet_with_lines(tmp_path: Path) -> None:
    path = tmp_path / "bom.xlsx"
    _write_workbook(path, {"template": [TITLE, HEADER, FOOTER], "data": [TITLE, HEADER, R40]})

    lines = read_bom(path)

    assert [line.refdes for line in lines] == [("R40",)]


def test_rejects_workbook_with_two_bom_sheets(tmp_path: Path) -> None:
    path = tmp_path / "bom.xlsx"
    _write_workbook(path, {"a": [HEADER, R40], "b": [HEADER, R63_R83]})

    with pytest.raises(ValueError, match="sheets"):
        read_bom(path)


def test_reconcile_reports_parts_missing_from_program() -> None:
    result = reconcile([_placement("R1")], [_line(("R1", "C18"), 2)])

    assert result.unplaced == ("C18",)


def test_reconcile_reports_parts_missing_from_bom() -> None:
    result = reconcile([_placement("R1"), _placement("SW6")], [_line(("R1",), 1)])

    assert result.unlisted == ("SW6",)


def test_reconcile_reports_quantity_mismatch() -> None:
    line = _line(("R12", "R84"), 1)

    result = reconcile([_placement("R12"), _placement("R84")], [line])

    assert result.quantity_mismatches == (line,)


def test_reconcile_sorts_refdes_naturally() -> None:
    result = reconcile([], [_line(("R10", "R2", "C1"), 3)])

    assert result.unplaced == ("C1", "R2", "R10")
