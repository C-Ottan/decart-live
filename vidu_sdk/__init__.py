"""Vidu S2-Editing Python SDK
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A high-level Python SDK for Reactor's real-time Vidu S2-Editing model.
Allows real-time webcam video stream editing, virtual try-on,
style transfer, character replacement, and background swapping.
"""

from .client import ViduS2Client
from .types import EditType, SessionPhase, SessionState, EditResult, SwitchResult
from .camera import WebcamStream, CameraAspectChecker
from .errors import ViduError, CommandError, CameraError, SessionError

__version__ = "1.0.0"

__all__ = [
    "ViduS2Client",
    "EditType",
    "SessionPhase",
    "SessionState",
    "EditResult",
    "SwitchResult",
    "WebcamStream",
    "CameraAspectChecker",
    "ViduError",
    "CommandError",
    "CameraError",
    "SessionError",
]
