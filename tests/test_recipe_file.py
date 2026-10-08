from pathlib import Path

import openpyxl
import pytest

from smd_vision_inspector.recipe import (
    BoardGeometry,
    OrientationCheck,
    Package,
    PartKind,
    load_library,
    load_recipe,
)

LIBRARY = """
packages:
  "1206": {size_mm: [3.2, 1.6], bom_tokens: ["1206"]}
  "1210": {size_mm: [3.2, 2.5], bom_tokens: ["1210"]}
  LQFP-48: {size_mm: [9.0, 9.0], polar: true}
footprints:
  IPC_1206: "1206"
  LQFP48: LQFP-48
"""

SSA = """[PCB]
Unit System = MILIMETER
Coordinate = LOWER LEFT

[BOARD]
Board Name = DEMO
PCB Size = 50.000, 30.000, 1.600

[PLACEMENTS]
"R1" 10.000 20.000 0.000 90.000 NONE 0 0 0 0 471 0 "10K" "" "IPC_1206"
"IC1" 30.000 15.000 0.000 270.000 NONE 0 0 0 0 471 0 "MCU" "" "LQFP48"
"C25" 5.000 5.000 0.000 0.000 NONE 0 0 0 0 471 0 "47UF" "" ""
"""

RECIPE = """
product: demo
board_size_mm: [50.0, 30.0]
geometry:
  panel_origin_mm: [-5.0, -5.0]
  panel_size_mm: [60.0, 40.0]
  fiducials_mm: [[2.0, 28.0], [48.0, 2.0], [10.0, 5.0], [40.0, 25.0]]
  fiducial_ring_mm: 1.95
library: ../library.yaml
programs: [demo.ssa]
bom: demo.xlsx
"""


@pytest.fixture
def recipe_dir(tmp_path: Path) -> Path:
    (tmp_path / "library.yaml").write_text(LIBRARY)
    product = tmp_path / "demo"
    product.mkdir()
    (product / "demo.ssa").write_text(SSA)

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.append(("Stok No", "Stok Adı", "Miktar", "Konum"))
    sheet.append(("H.E.KON.00093", "KOND 47UF 16V %10 X5R 1210 SMD", 1, "C25"))
    workbook.save(product / "demo.xlsx")

    return product


def test_loads_library(tmp_path: Path) -> None:
    path = tmp_path / "library.yaml"
    path.write_text(LIBRARY)

    library = load_library(path)

    assert library.packages["LQFP-48"] == Package("LQFP-48", (9.0, 9.0), polar=True)
    assert library.footprints["IPC_1206"] == "1206"


def test_library_rejects_footprint_of_unknown_package(tmp_path: Path) -> None:
    path = tmp_path / "library.yaml"
    path.write_text(LIBRARY + '  SOT23: "SOT-23"\n')

    with pytest.raises(ValueError, match="SOT-23"):
        load_library(path)


def test_recipe_builds_targets_relative_to_its_file(recipe_dir: Path) -> None:
    (recipe_dir / "recipe.yaml").write_text(RECIPE)

    recipe = load_recipe(recipe_dir / "recipe.yaml")

    assert recipe.product == "demo"
    assert recipe.board_size_mm == (50.0, 30.0)
    assert [(t.refdes, t.kind, t.package) for t in recipe.targets] == [
        ("R1", PartKind.RESISTOR, "1206"),
        ("IC1", PartKind.IC, "LQFP-48"),
        ("C25", PartKind.CAPACITOR, "1210"),
    ]


def test_recipe_reads_board_geometry(recipe_dir: Path) -> None:
    (recipe_dir / "recipe.yaml").write_text(RECIPE)

    recipe = load_recipe(recipe_dir / "recipe.yaml")

    assert recipe.geometry == BoardGeometry(
        panel_origin_mm=(-5.0, -5.0),
        panel_size_mm=(60.0, 40.0),
        fiducials_mm=((2.0, 28.0), (48.0, 2.0), (10.0, 5.0), (40.0, 25.0)),
        fiducial_ring_mm=1.95,
    )


def test_recipe_applies_overrides(recipe_dir: Path) -> None:
    overrides = "package_overrides: {R1: '1210'}\norientation_overrides: {IC1: half_turn}\n"
    (recipe_dir / "recipe.yaml").write_text(RECIPE + overrides)

    targets = {t.refdes: t for t in load_recipe(recipe_dir / "recipe.yaml").targets}

    assert targets["R1"].package == "1210"
    assert targets["IC1"].orientation is OrientationCheck.HALF_TURN


def test_recipe_rejects_unknown_key(recipe_dir: Path) -> None:
    (recipe_dir / "recipe.yaml").write_text(RECIPE + "thresholds: {}\n")

    with pytest.raises(ValueError, match="thresholds"):
        load_recipe(recipe_dir / "recipe.yaml")


def test_recipe_needs_four_fiducials_for_a_homography(recipe_dir: Path) -> None:
    text = RECIPE.replace(", [10.0, 5.0], [40.0, 25.0]", "")
    (recipe_dir / "recipe.yaml").write_text(text)

    with pytest.raises(ValueError, match="fiducials_mm"):
        load_recipe(recipe_dir / "recipe.yaml")
