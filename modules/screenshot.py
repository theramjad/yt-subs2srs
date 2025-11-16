"""Screenshot extraction using FFmpeg"""
import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def extract_screenshot(
    video_path: str,
    timestamp: float,
    output_path: str,
    resolution: str = "640x360"
) -> None:
    """
    Extract screenshot from video at timestamp

    Args:
        video_path: Path to video file
        timestamp: Time in seconds
        output_path: Output screenshot path
        resolution: Resolution (default 640x360)
    """
    cmd = [
        "ffmpeg",
        "-ss", str(timestamp),
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        "-s", resolution,
        "-y",
        output_path
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Screenshot saved: {output_path}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Screenshot extraction failed: {e.stderr}")
        raise Exception(f"Screenshot extraction failed")
