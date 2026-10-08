from pathlib import Path

import pytest

from smd_vision_inspector.recipe import Placement, merge_placements, parse_ssa, read_ssa

HEADER = """[VERSION]

[PCB]
Unit System = MILIMETER
Coordinate = LOWER LEFT
Rotation = 0
Placement Origin = , -10.000, 5.000
Fiducial = CIRCLE, 1.000, 2.000, 3.000, 4.000
Accept Mark = NONE, 0, 0
Bad Mark = NONE, 0, 0

[BOARD]
Board Name = DEMO
PCB Size = 50.000, 30.000, 1.600
Array = 1, 1, LOWER RIGHT
Array Offset = 0.000, 0.000

[PLACEMENTS]
"""

R1 = '"R1" 10.500 20.250 0.000 90.000 NONE 0 0 0 0 471 0 "10K%1" "" "IPC_1206"\n'
Q1_SKIPPED = '"Q1" 5.000 6.000 0.000 270.000 NONE 0 0 0 0 471 1 "BC817" "" "IPC_TRANSISTOR"\n'
Q1_PLACED = '"Q1" 5.000 6.000 0.000 270.000 NONE 0 0 0 0 2135 0 "BC817" "" "IPC_TRANSISTOR"\n'
C2_NO_FOOTPRINT = '"C2" 1.000 2.000 0.000 0.000 NONE 0 0 0 0 471 0 "47UF" "" ""\n'


def test_parses_placement_fields() -> None:
    program = parse_ssa(HEADER + R1)

    assert program.placements == (
        Placement(
            refdes="R1",
            x_mm=10.5,
            y_mm=20.25,
            rotation_deg=90.0,
            value="10K%1",
            footprint="IPC_1206",
        ),
    )


def test_keeps_empty_footprint() -> None:
    program = parse_ssa(HEADER + C2_NO_FOOTPRINT)

    assert program.placements[0].footprint == ""


def test_separates_skipped_placements() -> None:
    program = parse_ssa(HEADER + R1 + Q1_SKIPPED)

    assert [p.refdes for p in program.placements] == ["R1"]
    assert program.skipped == frozenset({"Q1"})


def test_reads_board_name_and_size() -> None:
    program = parse_ssa(HEADER + R1)

    assert program.board_name == "DEMO"
    assert program.size_mm == (50.0, 30.0)


def test_rejects_unsupported_unit() -> None:
    text = HEADER.replace("MILIMETER", "INCH") + R1

    with pytest.raises(ValueError, match="unit"):
        parse_ssa(text)


def test_rejects_unsupported_origin() -> None:
    text = HEADER.replace("LOWER LEFT", "UPPER LEFT") + R1

    with pytest.raises(ValueError, match="origin"):
        parse_ssa(text)


def test_rejects_truncated_placement() -> None:
    with pytest.raises(ValueError, match="R1"):
        parse_ssa(HEADER + '"R1" 10.500 20.250\n')


def test_merge_takes_skipped_part_from_other_machine() -> None:
    first = parse_ssa(HEADER + R1 + Q1_SKIPPED)
    second = parse_ssa(HEADER + Q1_PLACED)

    merged = merge_placements([first, second])

    assert sorted(p.refdes for p in merged) == ["Q1", "R1"]


def test_merge_rejects_part_placed_twice() -> None:
    first = parse_ssa(HEADER + R1)
    second = parse_ssa(HEADER + R1)

    with pytest.raises(ValueError, match="R1"):
        merge_placements([first, second])


def test_reads_windows_turkish_file(tmp_path: Path) -> None:
    path = tmp_path / "demo.ssa"
    path.write_bytes((HEADER + R1.replace("10K%1", "DİRENÇ")).encode("cp1254"))

    program = read_ssa(path)

    assert program.placements[0].value == "DİRENÇ"
