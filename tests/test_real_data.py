from pathlib import Path

import pytest

from smd_vision_inspector.recipe import merge_placements, read_bom, read_ssa, reconcile

pytestmark = pytest.mark.real_data

KARVOX = Path(__file__).parents[1] / "bom" / "karvox43"
KARVOX_PROGRAMS = ("SM471_62600BUTONLU.ssa", "SM482_62600BUTONLU.ssa")
KARVOX_SMD_COUNT = 204
KARVOX_BOM = "Y.E.KAY.66803.xlsx"


def _require(path: Path) -> Path:
    if not path.exists():
        pytest.skip(f"local data missing: {path}")
    return path


def test_karvox_programs_cover_every_smd_part_once() -> None:
    programs = [read_ssa(_require(KARVOX / name)) for name in KARVOX_PROGRAMS]

    refdes = {p.refdes for p in merge_placements(programs)}

    assert len(refdes) == KARVOX_SMD_COUNT
    assert "SW6" in refdes
    assert "U7" not in refdes


def test_karvox_bom_differs_from_button_variant_as_known() -> None:
    programs = [read_ssa(_require(KARVOX / name)) for name in KARVOX_PROGRAMS]
    bom = read_bom(_require(KARVOX / KARVOX_BOM))

    result = reconcile(merge_placements(programs), bom)

    # Through-hole parts and the touch variant's U7/U8/C18/C53.
    assert result.unplaced == ("C18", "C53", "KN1", "KN9", "RL1", "U7", "U8")
    assert result.unlisted == ("SW6", "SW7", "SW8", "SW9", "SW10")
    assert [line.refdes for line in result.quantity_mismatches] == [("R12", "R84")]
