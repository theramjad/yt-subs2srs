"""Video downloader using yt-dlp"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def download_video(youtube_url: str, output_dir: str) -> tuple[str, str]:
    """
    Download YouTube audio using yt-dlp (file named video.mp4 for compatibility)

    Args:
        youtube_url: YouTube video URL
        output_dir: Directory to save the audio file

    Returns:
        tuple: (audio_path, video_title)
    """
    logger.info(f"Downloading audio: {youtube_url}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    video_path = os.path.join(output_dir, "video.mp4")

    # Download audio only (best quality m4a/aac)
    cmd = [
        "yt-dlp",
        "--format", "ba[ext=m4a]/ba",
        "--output", video_path,
        youtube_url
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        logger.info("Audio downloaded successfully")

        # Get video title
        title_cmd = ["yt-dlp", "--get-title", youtube_url]
        title_result = subprocess.run(
            title_cmd,
            check=True,
            capture_output=True,
            text=True
        )
        title = title_result.stdout.strip()

        # Verify file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Downloaded: {title}")
        return video_path, title

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download video: {e.stderr}")
        raise Exception(f"Video download failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        raise
