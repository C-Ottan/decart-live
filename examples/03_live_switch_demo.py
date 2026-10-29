"""Example 03: Live Hot-Switching
Demonstrates switching reference image and editing type mid-session
without disconnecting or restarting the WebRTC stream.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidu_sdk import ViduS2Client, EditType

REACTOR_API_KEY = os.getenv("REACTOR_API_KEY", "rk_your_api_key_here")

# Two different styles to hot-swap between
STYLE_A_URL = "https://images.unsplash.com/photo-1579783902614-a3fb3927b675?w=800"  # Painting / Art
STYLE_B_URL = "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800"  # Cyberpunk / Neon


async def main():
    async with ViduS2Client(api_key=REACTOR_API_KEY) as client:
        print("Connected! Starting initial edit with Style A...")
        await client.start_edit(
            reference_image_url=STYLE_A_URL,
            editing_type=EditType.STYLE_TRANSFER
        )

        print("Streaming Style A for 10 seconds...")
        await asyncio.sleep(10)

        # Hot-switch to Style B live!
        print("\n[HOT-SWITCH] Switching reference image to Style B mid-session...")
        switch_res = await client.switch_reference(
            reference_image_url=STYLE_B_URL,
            editing_type=EditType.STYLE_TRANSFER
        )
        print(f"Switch acknowledged: reference_changed={switch_res.reference_changed}")

        print("Streaming Style B for 10 seconds...")
        await asyncio.sleep(10)

        # Hot-switch mode to background replacement!
        print("\n[HOT-SWITCH] Switching edit mode to Background Replacement...")
        switch_res_2 = await client.switch_reference(
            editing_type=EditType.BACKGROUND_REPLACEMENT
        )
        print(f"Mode switched to: {switch_res_2.editing_type}")

        await asyncio.sleep(5)
        print("\nEnding session...")


if __name__ == "__main__":
    asyncio.run(main())
