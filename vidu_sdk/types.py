"""Data models and enums for Vidu S2-Editing."""

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class EditType(str, Enum):
    """Supported editing modes for Vidu S2-Editing."""
    STYLE_TRANSFER = "style_transfer"
    VIRTUAL_TRYON = "virtual_tryon"
    SUBJECT_REPLACEMENT = "subject_replacement"
    BACKGROUND_REPLACEMENT = "background_replacement"


class SessionPhase(str, Enum):
    """Lifecycle phases of a Vidu S2 editing session."""
    IDLE = "idle"
    STARTING = "starting"
    WARMING_UP = "warming_up"
    LIVE = "live"
    ENDING = "ending"
    ENDED = "ended"
    FAILED = "failed"


class SessionState(BaseModel):
    """Authoritative snapshot of session state."""
    phase: SessionPhase = SessionPhase.IDLE
    camera_forwarding: bool = False
    video_receiving: bool = False
    editing_type: Optional[str] = None
    edit_max_seconds: Optional[int] = None
    end_reason: Optional[str] = None
    last_error: Optional[Any] = None
    raw: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionState":
        phase_str = data.get("phase", "idle")
        try:
            phase = SessionPhase(phase_str)
        except ValueError:
            phase = SessionPhase.IDLE

        # Normalize last_error
        err = data.get("last_error")
        if isinstance(err, dict):
            error_repr = f"[{err.get('code', 'ERROR')}] {err.get('reason', '')} (upstream {err.get('upstream_status', '')})".strip()
        else:
            error_repr = str(err) if err is not None else None

        return cls(
            phase=phase,
            camera_forwarding=bool(data.get("camera_forwarding", False)),
            video_receiving=bool(data.get("video_receiving", False)),
            editing_type=data.get("editing_type"),
            edit_max_seconds=data.get("edit_max_seconds"),
            end_reason=data.get("end_reason"),
            last_error=error_repr,
            raw=data,
        )


class EditResult(BaseModel):
    """Result returned when an edit ends."""
    end_reason: Optional[str] = None
    duration_seconds: float = 0.0


class SwitchResult(BaseModel):
    """Result returned after switching reference or editing type."""
    editing_type: Optional[str] = None
    reference_changed: bool = False
