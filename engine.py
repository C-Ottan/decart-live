"""DECART LIVE PRO - Streaming Engine.
Handles direct WebRTC streaming via Reactor / Decart API key.
"""

import asyncio
import os
import sys
from typing import Any, Callable, Optional
import numpy as np

from vidu_sdk import EditType, SessionPhase, ViduS2Client
from vidu_sdk.errors import ViduError


class StreamingEngine:
    """Manages direct WebRTC stream session with ViduS2Client using direct API Key."""

    def __init__(self):
        self.client: Optional[ViduS2Client] = None
        self.api_key: Optional[str] = None
        self.is_active = False

    async def start_session(
        self,
        api_key: str,
        reference_image: Optional[str],
        editing_type: str,
        zoom_factor: float,
        on_frame_cb: Callable[[np.ndarray], None],
        on_local_frame_cb: Callable[[np.ndarray], None],
        on_state_cb: Callable[[Any], None],
        on_error_cb: Callable[[Any], None],
    ):
        """Establish direct WebRTC connection with Reactor API key."""
        self.api_key = api_key.strip()
        if not self.api_key:
            raise ViduError("API Key cannot be empty. Please provide a valid Reactor/Decart API Key.")

        self.is_active = True

        # 1. Instantiate ViduS2Client directly with API Key
        self.client = ViduS2Client(api_key=self.api_key)

        # Wire callbacks
        self.client.on_frame(on_frame_cb)
        self.client.on_state(on_state_cb)
        self.client.on_error(on_error_cb)

        # 2. Connect to Reactor
        try:
            await self.client.connect()
        except Exception as err:
            err_str = str(err)
            if "credits_depleted" in err_str or "402" in err_str:
                raise ViduError("Reactor API Key has 0 credits. Add credits at reactor.inc/billing.")
            elif "peer connection" in err_str or "DisconnectedError" in err_str:
                raise ViduError("Reactor Connection Rejected: Peer connection busy or session limit reached.")
            raise

        # 3. Start camera stream with specified FOV zoom
        self.client.start_webcam_stream(
            camera_index=0,
            fps=30,
            zoom=zoom_factor,
            on_local_frame=on_local_frame_cb,
        )

        # 4. Start edit transformation with local reference image
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        bundled_asset = os.path.abspath(os.path.join(base_dir, "assets", "sample_reference.png"))
        if reference_image and os.path.exists(reference_image):
            await self.client.start_edit(reference_image=reference_image, editing_type=editing_type)
        elif os.path.exists(bundled_asset):
            await self.client.start_edit(reference_image=bundled_asset, editing_type=editing_type)
        else:
            fallback_img = np.zeros((512, 512, 3), dtype=np.uint8)
            fallback_img[:] = (120, 80, 220)
            import cv2
            cv2.circle(fallback_img, (256, 256), 150, (255, 200, 100), -1)
            _, buffer = cv2.imencode(".jpg", fallback_img)
            await self.client.start_edit(reference_image=buffer.tobytes(), editing_type=editing_type)

    async def stop_session(self):
        """Gracefully terminate stream session."""
        self.is_active = False
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
            self.client = None
