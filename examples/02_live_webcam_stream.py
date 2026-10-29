"""Example 02: Real-time Live Webcam Streaming
Captures frames from your local webcam, pushes them to Reactor,
and renders the incoming edited AI stream in an OpenCV window.
"""

import asyncio
import os
import sys
import cv2

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidu_sdk import ViduS2Client, EditType

REACTOR_API_KEY = os.getenv("REACTOR_API_KEY", "rk_your_api_key_here")

# Default local reference image (directly uploaded to Reactor)
DEFAULT_ASSET = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "sample_reference.png"))
REFERENCE_IMAGE = os.getenv("REFERENCE_IMAGE", DEFAULT_ASSET)


async def main():
    client = ViduS2Client(api_key=REACTOR_API_KEY)

    # Frame buffer to hold the latest AI-edited frame
    latest_edited_frame = None

    @client.on_frame
    def on_edited_frame(rgb_frame):
        nonlocal latest_edited_frame
        # Convert RGB back to BGR for OpenCV display
        latest_edited_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

    @client.on_state
    def on_state(state):
        print(f"Status update -> Phase: {state.phase.value} | Video receiving: {state.video_receiving}")

    print("Connecting to Reactor...")
    await client.connect()

    latest_local_frame = None

    def on_local_webcam(rgb_frame):
        nonlocal latest_local_frame
        latest_local_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

    # 1. Start streaming local webcam to the 'camera' track
    print("Starting webcam stream (camera index 0)...")
    client.start_webcam_stream(camera_index=0, fps=30, on_local_frame=on_local_webcam)

    # 2. Trigger start_edit
    print("Starting real-time edit...")
    if REFERENCE_IMAGE.startswith("http"):
        await client.start_edit(reference_image_url=REFERENCE_IMAGE, editing_type=EditType.STYLE_TRANSFER)
    else:
        await client.start_edit(reference_image=REFERENCE_IMAGE, editing_type=EditType.STYLE_TRANSFER)

    print("\n[STREAMING ACTIVE] Press 'q' in the video window to stop streaming.")

    # 3. Main GUI rendering loop
    try:
        while True:
            display_frame = None
            if latest_edited_frame is not None:
                display_frame = latest_edited_frame.copy()
                # Picture-in-picture: show small local camera thumbnail in bottom-right corner
                if latest_local_frame is not None:
                    pip = cv2.resize(latest_local_frame, (190, 108))
                    display_frame[-118:-10, -200:-10] = pip
                    cv2.rectangle(display_frame, (-200, -118), (-10, -10), (0, 255, 128), 1)
            elif latest_local_frame is not None:
                display_frame = latest_local_frame.copy()
                # Show status overlay on local camera while waiting for AI output
                overlay_text = f"Phase: {client.state.phase.value.upper()} (Connecting AI...)"
                cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 40), (0, 0, 0), -1)
                cv2.putText(display_frame, overlay_text, (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 128), 2)
            else:
                placeholder = np.zeros((544, 952, 3), dtype=np.uint8)
                status_txt = f"Connecting to Reactor... Phase: {client.state.phase.value}"
                cv2.putText(placeholder, status_txt, (180, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 128), 2)
                display_frame = placeholder

            cv2.imshow("Vidu S2 Realtime Edited Output", display_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break

            await asyncio.sleep(0.01)
    finally:
        print("\nStopping stream and disconnecting...")
        cv2.destroyAllWindows()
        await client.disconnect()
        print("Done.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStreaming stopped by user.")
