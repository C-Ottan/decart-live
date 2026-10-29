"""Example 01: Basic Edit with Vidu S2-Editing
Demonstrates connecting, starting an edit with a reference image URL,
and monitoring session lifecycle phases.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidu_sdk import ViduS2Client, EditType, SessionPhase

# Replace with your Reactor API key (or set REACTOR_API_KEY environment variable)
REACTOR_API_KEY = os.getenv("REACTOR_API_KEY", "rk_your_api_key_here")

# Default local reference image
DEFAULT_ASSET = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sample_reference.png"))
REFERENCE_IMAGE = os.getenv("REFERENCE_IMAGE", DEFAULT_ASSET)


async def main():
    print("Initializing Vidu S2-Editing client...")
    client = ViduS2Client(api_key=REACTOR_API_KEY)

    @client.on_state
    def on_state(state):
        print(f"-> Phase: {state.phase.value} | Camera forwarding: {state.camera_forwarding} | Video receiving: {state.video_receiving}")

    @client.on_error
    def on_error(err):
        print(f"-> [Command Error] {err.code}: {err.reason}")

    # Connect to Reactor session
    await client.connect()
    print("Connected! Initial state:", client.state.phase.value)

    # Start webcam capture so camera frames reach the model immediately
    print("Starting camera stream...")
    client.start_webcam_stream(camera_index=0, fps=30)

    # Start edit by uploading the local image
    print("Starting edit (uploading reference image)...")
    if os.path.exists(REFERENCE_IMAGE):
        await client.start_edit(reference_image=REFERENCE_IMAGE, editing_type=EditType.STYLE_TRANSFER)
    else:
        await client.start_edit(reference_image_url="https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800", editing_type=EditType.STYLE_TRANSFER)

    # Keep session alive for 20 seconds
    print("Edit running. Monitoring for 20 seconds...")
    await asyncio.sleep(20)

    # Gracefully end the edit
    print("Ending edit...")
    result = await client.end_edit()
    print(f"Edit ended! Duration: {result.duration_seconds}s | Reason: {result.end_reason}")

    await client.disconnect()
    print("Disconnected.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nSession stopped by user.")
