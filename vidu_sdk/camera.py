"""Camera capture and aspect ratio tools for Vidu S2-Editing."""

import asyncio
import time
from typing import Callable, Optional, Tuple
import cv2
import numpy as np

from .errors import CameraError


class CameraAspectChecker:
    """Helper to inspect webcam resolution and check aspect ratio for Vidu S2."""
    TARGET_WIDTH = 952
    TARGET_HEIGHT = 544
    TARGET_ASPECT = TARGET_WIDTH / TARGET_HEIGHT  # 7:4 = 1.75

    @classmethod
    def test_camera(cls, camera_index: int = 0) -> dict:
        """Probe camera to get native resolution and aspect ratio score."""
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return {
                "available": False,
                "error": f"Cannot open camera index {camera_index}"
            }

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            return {
                "available": False,
                "error": "Failed to read test frame from camera"
            }

        aspect = width / height if height > 0 else 0
        aspect_diff = abs(aspect - cls.TARGET_ASPECT)

        return {
            "available": True,
            "width": width,
            "height": height,
            "fps": fps,
            "aspect_ratio": round(aspect, 3),
            "target_aspect_ratio": round(cls.TARGET_ASPECT, 3),
            "aspect_difference": round(aspect_diff, 3),
            "recommended_scale": f"{cls.TARGET_WIDTH}x{cls.TARGET_HEIGHT} (7:4)",
        }


class WebcamStream:
    """Asynchronous webcam streamer that captures and pipes frames to Reactor camera track."""

    def __init__(
        self,
        camera_index: int = 0,
        fps: int = 30,
        target_size: Optional[Tuple[int, int]] = (952, 544),
        zoom: float = 0.5,
    ):
        self.camera_index = camera_index
        self.fps = fps
        self.frame_interval = 1.0 / fps
        self.target_size = target_size or (952, 544)
        self.zoom = zoom
        self._cap: Optional[cv2.VideoCapture] = None
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._on_local_frame: Optional[Callable[[np.ndarray], None]] = None

    def set_zoom(self, zoom: float):
        """Set zoom factor dynamically (e.g. 0.5 for 0.5x ultra-wide)."""
        self.zoom = max(0.2, min(1.0, float(zoom)))

    def start(self):
        """Open the camera device."""
        if self._running:
            return

        self._cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not self._cap or not self._cap.isOpened():
            self._cap = cv2.VideoCapture(self.camera_index)

        if not self._cap.isOpened():
            raise CameraError(f"Could not open webcam index {self.camera_index}")

        # Request standard resolution
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        self._running = True

    def read_rgb_frame(self) -> Optional[np.ndarray]:
        """Read a single frame from the camera with ultra-wide framing applied."""
        if not self._cap or not self._cap.isOpened():
            return None

        ret, frame = self._cap.read()
        if not ret or frame is None:
            return None

        h, w = frame.shape[:2]
        target_w, target_h = self.target_size if self.target_size else (952, 544)

        if self.target_size:
            # Proportional crisp center-crop to 7:4 widescreen without artificial darkening
            scale = max(target_w / w, target_h / h)
            nw, nh = int(w * scale), int(h * scale)
            resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
            y_crop = max(0, (nh - target_h) // 2)
            x_crop = max(0, (nw - target_w) // 2)
            frame = resized[y_crop : y_crop + target_h, x_crop : x_crop + target_w]

        # Convert BGR to RGB for Reactor track
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return rgb_frame

    async def pipe_to(self, track, on_frame: Optional[Callable[[np.ndarray], None]] = None):
        """Continuously capture frames and push them into the Reactor track."""
        self.start()
        self._on_local_frame = on_frame

        # Ensure track is published before pushing frames
        if hasattr(track, "published") and not track.published:
            if hasattr(track, "publish") and asyncio.iscoroutinefunction(track.publish):
                await track.publish()

        frame_count = 0
        try:
            while self._running:
                t0 = time.perf_counter()
                frame = self.read_rgb_frame()
                if frame is not None:
                    try:
                        # Push frame to Reactor track
                        track.push_frame(frame)
                        frame_count += 1
                        if frame_count % 90 == 0:
                            print(f"[WebcamStream] Pushed {frame_count} frames to model...")
                    except Exception as push_err:
                        print(f"[WebcamStream Error] Failed to push frame: {push_err}")

                    if self._on_local_frame:
                        self._on_local_frame(frame)

                elapsed = time.perf_counter() - t0
                sleep_time = max(0.001, self.frame_interval - elapsed)
                await asyncio.sleep(sleep_time)
        except asyncio.CancelledError:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop camera streaming and release resources."""
        self._running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None
