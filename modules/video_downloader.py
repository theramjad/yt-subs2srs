"""Video downloader using yt-dlp"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def download_video(youtube_url: str, output_dir: str) -> tuple[str, str]:
    """
    Download YouTube video at 360p using yt-dlp

    Args:
        youtube_url: YouTube video URL
        output_dir: Directory to save the video

    Returns:
        tuple: (video_path, video_title)
    """
    logger.info(f"Downloading video: {youtube_url}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    video_path = os.path.join(output_dir, "video.mp4")

    # Download video with yt-dlp
    # Format: 360p combined or separate video+audio, with fallbacks
    cmd = [
        "yt-dlp",
        "--format", "18/bv*[height<=360]+ba/b[height<=360]/bv*+ba/b",
        "--merge-output-format", "mp4",
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

        logger.info("Video downloaded successfully")

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
