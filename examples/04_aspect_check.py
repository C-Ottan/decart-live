"""Example 04: Camera Aspect Ratio and Diagnostic Tool
Inspects connected webcam, tests resolution, and checks aspect ratio match
against Vidu S2-Editing's native output (7:4, 952x544).
"""

import os
import sys

# Allow running directly from repo root or examples folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from vidu_sdk import CameraAspectChecker


def main():
    print("=" * 60)
    print("Vidu S2-Editing: Webcam Aspect Ratio Diagnostic Tool")
    print("=" * 60)

    # Test camera index 0
    info = CameraAspectChecker.test_camera(camera_index=0)

    if not info.get("available"):
        print(f"Error: {info.get('error')}")
        return

    print(f"Camera Status:             ONLINE")
    print(f"Native Resolution:         {info['width']} x {info['height']}")
    print(f"Frame Rate (FPS):          {info['fps']}")
    print(f"Camera Aspect Ratio:       {info['aspect_ratio']}:1")
    print(f"Vidu Target Aspect Ratio:  {info['target_aspect_ratio']}:1 (7:4)")
    print(f"Aspect Delta:              {info['aspect_difference']}")
    print(f"Target Render Size:        {info['recommended_scale']}")
    print("-" * 60)

    if info["aspect_difference"] < 0.1:
        print("Great! Your camera aspect ratio closely matches Vidu's native 7:4.")
    else:
        print("Note: The SDK will automatically scale and fit your camera frames to 952x544.")
    print("=" * 60)


if __name__ == "__main__":
    main()
