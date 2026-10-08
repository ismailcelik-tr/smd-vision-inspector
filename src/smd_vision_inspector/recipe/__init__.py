"""Product recipe: what is placed where, and how to inspect it."""

from smd_vision_inspector.recipe.bom import (
    BomLine,
    Reconciliation,
    parse_bom_rows,
    read_bom,
    reconcile,
)
from smd_vision_inspector.recipe.loader import Recipe, load_library, load_recipe
from smd_vision_inspector.recipe.packages import Package, PackageLibrary
from smd_vision_inspector.recipe.parts import PartKind, kind_of
from smd_vision_inspector.recipe.placement import Placement
from smd_vision_inspector.recipe.ssa import SsaProgram, merge_placements, parse_ssa, read_ssa
from smd_vision_inspector.recipe.targets import InspectionTarget, OrientationCheck, build_targets

__all__ = [
    "BomLine",
    "InspectionTarget",
    "OrientationCheck",
    "Package",
    "PackageLibrary",
    "PartKind",
    "Placement",
    "Recipe",
    "Reconciliation",
    "SsaProgram",
    "build_targets",
    "kind_of",
    "load_library",
    "load_recipe",
    "merge_placements",
    "parse_bom_rows",
    "parse_ssa",
    "read_bom",
    "read_ssa",
    "reconcile",
]
