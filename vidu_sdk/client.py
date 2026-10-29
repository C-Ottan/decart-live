"""High-level client for Vidu S2-Editing on Reactor."""

import asyncio
import os
from pathlib import Path
from typing import Any, BinaryIO, Callable, Optional, Union
import numpy as np
from reactor_sdk import Reactor

from .types import EditType, SessionPhase, SessionState, EditResult, SwitchResult
from .errors import CommandError, SessionError, ViduError
from .camera import WebcamStream


class ViduS2Client:
    """High-level client for Reactor's real-time Vidu S2-Editing model.

    Example:
        async with ViduS2Client(api_key="rk_...") as client:
            @client.on_frame
            def handle_frame(rgb_frame):
                # Render incoming edited frame
                pass

            await client.start_edit(
                reference_image="path/to/style.jpg",
                editing_type=EditType.STYLE_TRANSFER
            )
            # Stream camera frames...
    """

    MODEL_NAME = "reactor/vidu-s2-editing"

    def __init__(
        self,
        api_key: Optional[str] = None,
        jwt: Optional[str] = None,
        api_url: str = "https://api.reactor.inc",
    ):
        """Initialize ViduS2Client with an API key (rk_...) or pre-generated JWT."""
        self.api_key = api_key or os.getenv("REACTOR_API_KEY")
        self.jwt = jwt
        self.api_url = api_url

        if not self.api_key and not self.jwt:
            raise ViduError("Either api_key or jwt must be provided.")

        self._reactor: Optional[Reactor] = None
        self._state = SessionState()
        self._is_connected = False
        self._is_live = False

        # WebRTC tracks
        self._camera_track = None
        self._main_video_track = None

        # Camera streaming task
        self._webcam_stream: Optional[WebcamStream] = None
        self._webcam_task: Optional[asyncio.Task] = None

        # Event callbacks
        self._frame_callbacks: list[Callable[[np.ndarray], None]] = []
        self._state_callbacks: list[Callable[[SessionState], None]] = []
        self._error_callbacks: list[Callable[[CommandError], None]] = []
        self._status_callbacks: list[Callable[[str], None]] = []

    @property
    def state(self) -> SessionState:
        """Get the latest recorded session state."""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if connected to the Reactor session."""
        return self._is_connected

    @property
    def is_live(self) -> bool:
        """Check if the session is currently live and editing."""
        return self._is_live

    def on_frame(self, callback: Callable[[np.ndarray], None]) -> Callable[[np.ndarray], None]:
        """Register a callback for incoming edited video frames from main_video."""
        self._frame_callbacks.append(callback)
        return callback

    def on_state(self, callback: Callable[[SessionState], None]) -> Callable[[SessionState], None]:
        """Register a callback for session_state updates."""
        self._state_callbacks.append(callback)
        return callback

    def on_error(self, callback: Callable[[CommandError], None]) -> Callable[[CommandError], None]:
        """Register a callback for command_error events."""
        self._error_callbacks.append(callback)
        return callback

    def on_status(self, callback: Callable[[str], None]) -> Callable[[str], None]:
        """Register a callback for connection status updates."""
        self._status_callbacks.append(callback)
        return callback

    async def connect(self) -> "ViduS2Client":
        """Connect to the Reactor backend and setup media tracks."""
        if self._is_connected and self._reactor:
            return self

        self._reactor = Reactor(
            model_name=self.MODEL_NAME,
            api_key=self.api_key,
            jwt=self.jwt,
            api_url=self.api_url,
        )

        # Wire up message listener
        @self._reactor.on_message
        def _handle_message(msg: dict[str, Any]):
            msg_type = msg.get("type")
            data = msg.get("data", {})

            if msg_type == "session_state":
                self._state = SessionState.from_dict(data)
                self._is_live = (self._state.phase == SessionPhase.LIVE)
                for cb in self._state_callbacks:
                    try:
                        cb(self._state)
                    except Exception as e:
                        print(f"[ViduSDK] State callback error: {e}")

            elif msg_type == "command_error":
                err = CommandError(code=data.get("code", "UNKNOWN"), reason=data.get("reason"))
                for cb in self._error_callbacks:
                    try:
                        cb(err)
                    except Exception as e:
                        print(f"[ViduSDK] Error callback error: {e}")

        # Wire up status listener
        @self._reactor.on_status
        def _handle_status(status):
            status_str = str(status)
            for cb in self._status_callbacks:
                try:
                    cb(status_str)
                except Exception as e:
                    print(f"[ViduSDK] Status callback error: {e}")

        await self._reactor.connect()
        self._is_connected = True

        # Grab tracks
        self._camera_track = self._reactor.track("camera")
        self._main_video_track = self._reactor.track("main_video")

        # Publish camera track so it is immediately active and ready to stream
        try:
            await self._camera_track.publish()
        except Exception as e:
            print(f"[ViduSDK] Initial camera publish note: {e}")

        # Register frame receiver on main_video
        @self._main_video_track.on_frame
        def _handle_frame(frame: np.ndarray):
            for cb in self._frame_callbacks:
                try:
                    cb(frame)
                except Exception as e:
                    print(f"[ViduSDK] Frame callback error: {e}")

        return self

    async def ensure_camera_published(self):
        """Ensure the camera track is published to Reactor."""
        if not self._camera_track:
            raise SessionError("Camera track not found. Call connect() first.")
        if not self._camera_track.published:
            await self._camera_track.publish()

    def push_camera_frame(self, frame: np.ndarray):
        """Push a single RGB frame into the camera input track."""
        if not self._camera_track:
            raise SessionError("Camera track is not initialized.")
        self._camera_track.push_frame(frame)

    @staticmethod
    def _optimize_image_payload(image_input: Union[str, Path, bytes, BinaryIO]) -> Union[str, Path, bytes, BinaryIO]:
        """Resize large images down to max 1024px to dramatically speed up upload and AI startup."""
        try:
            import io
            from PIL import Image

            if isinstance(image_input, (str, Path)) and os.path.exists(str(image_input)):
                img = Image.open(str(image_input))
            elif isinstance(image_input, bytes):
                img = Image.open(io.BytesIO(image_input))
            else:
                return image_input

            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            w, h = img.size
            max_dim = 1024
            if max(w, h) > max_dim:
                ratio = max_dim / max(w, h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=88, optimize=True)
            return buf.getvalue()
        except Exception as e:
            print(f"[ViduSDK] Image optimization skipped: {e}")
            return image_input

    async def start_edit(
        self,
        reference_image: Optional[Union[str, Path, bytes, BinaryIO]] = None,
        reference_image_url: Optional[str] = None,
        editing_type: Union[EditType, str] = EditType.STYLE_TRANSFER,
    ):
        """Start a video edit session with a reference image and editing type.

        Args:
            reference_image: Local image file path, bytes, or file-like object.
            reference_image_url: Public HTTP/HTTPS URL of reference image.
            editing_type: Edit mode: style_transfer, virtual_tryon, subject_replacement, or background_replacement.
        """
        if not self._is_connected:
            await self.connect()

        # Ensure camera track is published
        await self.ensure_camera_published()

        payload: dict[str, Any] = {}

        if isinstance(editing_type, EditType):
            payload["editing_type"] = editing_type.value
        else:
            payload["editing_type"] = str(editing_type)

        if reference_image is not None and reference_image_url is not None:
            raise ViduError("Provide either reference_image OR reference_image_url, not both.")

        if reference_image is not None:
            fast_ref = self._optimize_image_payload(reference_image)
            if isinstance(fast_ref, bytes):
                uploaded_ref = await self._reactor.upload_file(fast_ref, name="ref.jpg", mime_type="image/jpeg")
            else:
                uploaded_ref = await self._reactor.upload_file(fast_ref)
            payload["reference_image"] = uploaded_ref
        elif reference_image_url is not None:
            payload["reference_image_url"] = reference_image_url
        else:
            raise ViduError("Either reference_image or reference_image_url must be provided.")

        # Send start_edit
        await self._reactor.send_command("start_edit", payload)

    async def switch_reference(
        self,
        reference_image: Optional[Union[str, Path, bytes, BinaryIO]] = None,
        reference_image_url: Optional[str] = None,
        editing_type: Optional[Union[EditType, str]] = None,
    ) -> SwitchResult:
        """Hot-swap reference image or edit mode live while the stream is running."""
        if not self._is_connected or not self._reactor:
            raise SessionError("Cannot switch reference when disconnected.")

        payload: dict[str, Any] = {}

        if reference_image is not None and reference_image_url is not None:
            raise ViduError("Provide either reference_image OR reference_image_url, not both.")

        if reference_image is not None:
            fast_ref = self._optimize_image_payload(reference_image)
            if isinstance(fast_ref, bytes):
                uploaded_ref = await self._reactor.upload_file(fast_ref, name="ref.jpg", mime_type="image/jpeg")
            else:
                uploaded_ref = await self._reactor.upload_file(fast_ref)
            payload["reference_image"] = uploaded_ref
        elif reference_image_url is not None:
            payload["reference_image_url"] = reference_image_url

        if editing_type is not None:
            payload["editing_type"] = editing_type.value if isinstance(editing_type, EditType) else str(editing_type)

        if not payload:
            raise ViduError("switch_reference requires at least one parameter to update.")

        reply = await self._reactor.send_command("switch_reference", payload)
        data = reply.get("data", {}) if reply else {}
        return SwitchResult(
            editing_type=data.get("editing_type"),
            reference_changed=bool(data.get("reference_changed", False)),
        )

    async def end_edit(self) -> EditResult:
        """End the current active edit, keeping the session ready for future edits."""
        if not self._is_connected or not self._reactor:
            return EditResult()

        reply = await self._reactor.send_command("end_edit", {})
        self._is_live = False
        data = reply.get("data", {}) if reply else {}
        return EditResult(
            end_reason=data.get("end_reason"),
            duration_seconds=float(data.get("duration_seconds", 0.0)),
        )

    async def get_state(self) -> SessionState:
        """Fetch the authoritative session state snapshot."""
        if not self._is_connected or not self._reactor:
            return self._state

        reply = await self._reactor.send_command("get_state", {})
        data = reply.get("data", {}) if reply else {}
        self._state = SessionState.from_dict(data)
        return self._state

    def start_webcam_stream(
        self,
        camera_index: int = 0,
        fps: int = 30,
        target_size: tuple[int, int] = (952, 544),
        zoom: float = 0.5,
        on_local_frame: Optional[Callable[[np.ndarray], None]] = None,
    ) -> asyncio.Task:
        """Start capturing local webcam frames and streaming directly into the camera track."""
        if not self._camera_track:
            raise SessionError("Camera track is not available. Call connect() first.")

        self.stop_webcam_stream()

        self._webcam_stream = WebcamStream(
            camera_index=camera_index,
            fps=fps,
            target_size=target_size,
            zoom=zoom,
        )

        self._webcam_task = asyncio.create_task(
            self._webcam_stream.pipe_to(self._camera_track, on_frame=on_local_frame)
        )


        def _on_webcam_done(t: asyncio.Task):
            if not t.cancelled():
                exc = t.exception()
                if exc:
                    print(f"[WebcamStream Error] Task stopped with exception: {exc}")

        self._webcam_task.add_done_callback(_on_webcam_done)
        return self._webcam_task

    def set_webcam_zoom(self, zoom: float):
        """Update camera zoom / FOV factor dynamically on active stream."""
        if self._webcam_stream:
            self._webcam_stream.set_zoom(zoom)

    def stop_webcam_stream(self):
        """Stop local webcam capture task."""
        if self._webcam_stream:
            self._webcam_stream.stop()
            self._webcam_stream = None

        if self._webcam_task and not self._webcam_task.done():
            self._webcam_task.cancel()
            self._webcam_task = None

    async def disconnect(self):
        """Disconnect session and cleanup streams."""
        self.stop_webcam_stream()

        if self._reactor:
            if self._is_live:
                try:
                    await self.end_edit()
                except Exception:
                    pass
            await self._reactor.disconnect()
            self._reactor.close()
            self._reactor = None

        self._is_connected = False
        self._is_live = False

    async def __aenter__(self) -> "ViduS2Client":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
