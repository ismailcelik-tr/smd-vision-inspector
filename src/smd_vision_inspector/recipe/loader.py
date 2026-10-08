"""Recipe and package library files (YAML)."""

from dataclasses import dataclass
from pathlib import Path
from typing import Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from smd_vision_inspector.recipe.bom import read_bom
from smd_vision_inspector.recipe.packages import Package, PackageLibrary
from smd_vision_inspector.recipe.ssa import merge_placements, read_ssa
from smd_vision_inspector.recipe.targets import InspectionTarget, OrientationCheck, build_targets

__all__ = ["Recipe", "load_library", "load_recipe"]


@dataclass(frozen=True, slots=True)
class Recipe:
    product: str
    board_size_mm: tuple[float, float]
    targets: tuple[InspectionTarget, ...]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class _PackageEntry(_Strict):
    size_mm: tuple[float, float]
    polar: bool = False
    bom_tokens: tuple[str, ...] = ()


class _LibraryFile(_Strict):
    packages: dict[str, _PackageEntry]
    footprints: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _footprints_name_known_packages(self) -> Self:
        unknown = sorted(set(self.footprints.values()) - set(self.packages))
        if unknown:
            raise ValueError(f"footprints map to unknown packages: {', '.join(unknown)}")
        return self


class _RecipeFile(_Strict):
    product: str
    board_size_mm: tuple[float, float]
    library: Path
    programs: list[Path] = Field(min_length=1)
    bom: Path | None = None
    package_overrides: dict[str, str] = Field(default_factory=dict)
    orientation_overrides: dict[str, OrientationCheck] = Field(default_factory=dict)


def load_library(path: Path) -> PackageLibrary:
    file = _LibraryFile.model_validate(_read_yaml(path))
    packages = {
        name: Package(name, entry.size_mm, entry.polar, entry.bom_tokens)
        for name, entry in file.packages.items()
    }
    return PackageLibrary(packages=packages, footprints=file.footprints)


def load_recipe(path: Path) -> Recipe:
    """Paths inside the recipe are relative to its own folder."""
    file = _RecipeFile.model_validate(_read_yaml(path))
    base = path.parent

    placements = merge_placements(read_ssa(base / program) for program in file.programs)
    bom = read_bom(base / file.bom) if file.bom else ()
    targets = build_targets(
        placements,
        bom,
        load_library(base / file.library),
        file.package_overrides,
        file.orientation_overrides,
    )

    return Recipe(product=file.product, board_size_mm=file.board_size_mm, targets=targets)


def _read_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as stream:
        return yaml.safe_load(stream)
