"""Part kinds derived from reference designators."""

import re
from enum import StrEnum

__all__ = ["PartKind", "kind_of"]


class PartKind(StrEnum):
    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    LED = "led"
    TRANSISTOR = "transistor"
    IC = "ic"
    CRYSTAL = "crystal"
    CONNECTOR = "connector"
    SWITCH = "switch"


_PREFIXES = {
    "R": PartKind.RESISTOR,
    "C": PartKind.CAPACITOR,
    "L": PartKind.INDUCTOR,
    "LED": PartKind.LED,
    "D": PartKind.DIODE,
    "Z": PartKind.DIODE,
    "TVS": PartKind.DIODE,
    "Q": PartKind.TRANSISTOR,
    "U": PartKind.IC,
    "IC": PartKind.IC,
    "X": PartKind.CRYSTAL,
    "P": PartKind.CONNECTOR,
    "SW": PartKind.SWITCH,
}


def kind_of(refdes: str) -> PartKind:
    match = re.match(r"[A-Za-z]+", refdes)
    kind = _PREFIXES.get(match.group().upper()) if match else None
    if kind is None:
        raise ValueError(f"unknown refdes prefix: {refdes}")

    return kind
