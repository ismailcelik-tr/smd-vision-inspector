import pytest

from smd_vision_inspector.recipe import (
    BomLine,
    OrientationCheck,
    Package,
    PackageLibrary,
    PartKind,
    Placement,
    build_targets,
    kind_of,
)

CHIP_1206 = Package("1206", (3.2, 1.6), bom_tokens=("1206",))
CHIP_1210 = Package("1210", (3.2, 2.5), bom_tokens=("1210",))
ELKO = Package("CAP-ELEC-6.3", (6.6, 6.6), polar=True)
LQFP48 = Package("LQFP-48", (9.0, 9.0), polar=True)

LIBRARY = PackageLibrary(
    packages={p.name: p for p in (CHIP_1206, CHIP_1210, ELKO, LQFP48)},
    footprints={
        "IPC_1206": "1206",
        "LED_1206": "1206",
        "SMD_ELK_CAP_6.3*5.4": "CAP-ELEC-6.3",
        "LQFP48": "LQFP-48",
    },
)


def _placement(refdes: str, footprint: str, x: float = 1.0, y: float = 2.0) -> Placement:
    return Placement(refdes, x, y, 90.0, "", footprint)


def _bom(refdes: str, description: str) -> BomLine:
    return BomLine("H.E.X", description, 1, (refdes,))


@pytest.mark.parametrize(
    ("refdes", "kind"),
    [
        ("R12", PartKind.RESISTOR),
        ("C4", PartKind.CAPACITOR),
        ("L3", PartKind.INDUCTOR),
        ("LED2", PartKind.LED),
        ("D1", PartKind.DIODE),
        ("Z2", PartKind.DIODE),
        ("TVS1", PartKind.DIODE),
        ("Q16", PartKind.TRANSISTOR),
        ("U1", PartKind.IC),
        ("IC2", PartKind.IC),
        ("X1", PartKind.CRYSTAL),
        ("P1", PartKind.CONNECTOR),
        ("SW6", PartKind.SWITCH),
    ],
)
def test_kind_from_refdes_prefix(refdes: str, kind: PartKind) -> None:
    assert kind_of(refdes) is kind


def test_unknown_refdes_prefix_raises() -> None:
    with pytest.raises(ValueError, match="BAT1"):
        kind_of("BAT1")


def test_target_carries_placement_geometry() -> None:
    [target] = build_targets([_placement("R1", "IPC_1206", x=10.5, y=20.25)], [], LIBRARY)

    assert target.refdes == "R1"
    assert target.package == "1206"
    assert target.center_mm == (10.5, 20.25)
    assert target.rotation_deg == 90.0
    assert target.size_mm == (3.2, 1.6)


def test_package_from_bom_when_footprint_unknown() -> None:
    placement = _placement("C25", "")
    bom = [_bom("C25", "KOND 47UF 16V %10 X5R 1210 SMD")]

    [target] = build_targets([placement], bom, LIBRARY)

    assert target.package == "1210"


def test_override_beats_footprint() -> None:
    [target] = build_targets(
        [_placement("R1", "IPC_1206")], [], LIBRARY, package_overrides={"R1": "1210"}
    )

    assert target.package == "1210"


def test_unresolved_packages_are_listed_together() -> None:
    placements = [_placement("R1", "UNKNOWN"), _placement("R2", ""), _placement("R3", "IPC_1206")]

    with pytest.raises(ValueError, match="R1, R2"):
        build_targets(placements, [], LIBRARY)


@pytest.mark.parametrize(
    ("refdes", "footprint", "check"),
    [
        ("R1", "IPC_1206", OrientationCheck.NONE),
        ("C1", "IPC_1206", OrientationCheck.NONE),
        ("LED1", "LED_1206", OrientationCheck.HALF_TURN),
        ("C4", "SMD_ELK_CAP_6.3*5.4", OrientationCheck.QUARTER_TURN),
        ("IC1", "LQFP48", OrientationCheck.QUARTER_TURN),
    ],
)
def test_orientation_check_by_kind_and_package(
    refdes: str, footprint: str, check: OrientationCheck
) -> None:
    [target] = build_targets([_placement(refdes, footprint)], [], LIBRARY)

    assert target.orientation is check


def test_orientation_override_beats_kind() -> None:
    # Bidirectional TVS diodes look the same both ways.
    [target] = build_targets(
        [_placement("TVS1", "IPC_1206")],
        [],
        LIBRARY,
        orientation_overrides={"TVS1": OrientationCheck.NONE},
    )

    assert target.orientation is OrientationCheck.NONE
