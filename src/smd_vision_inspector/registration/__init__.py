"""Align a board photo to board millimetres."""

from smd_vision_inspector.registration.fiducial import FiducialHit, locate_fiducial
from smd_vision_inspector.registration.frame import CanonicalFrame
from smd_vision_inspector.registration.register import (
    Registration,
    RegistrationError,
    panel_frame,
    register,
    warp_to_canonical,
)

__all__ = [
    "CanonicalFrame",
    "FiducialHit",
    "Registration",
    "RegistrationError",
    "locate_fiducial",
    "panel_frame",
    "register",
    "warp_to_canonical",
]
