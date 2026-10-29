"""Exceptions for Vidu S2-Editing SDK."""

class ViduError(Exception):
    """Base exception for all Vidu SDK errors."""
    pass


class CommandError(ViduError):
    """Raised when the Reactor model rejects a command."""
    def __init__(self, code: str, reason: str | None = None):
        self.code = code
        self.reason = reason or "Unknown command error"
        super().__init__(f"[{self.code}] {self.reason}")


class SessionError(ViduError):
    """Raised when an operation is invalid for the current session state."""
    pass


class CameraError(ViduError):
    """Raised when there is an issue with the camera stream or capture."""
    pass
