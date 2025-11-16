"""Video downloader using yt-dlp"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_video_title(youtube_url: str) -> str:
    """
    Get video title from YouTube URL

    Args:
        youtube_url: YouTube video URL

    Returns:
        str: Video title
    """
    title_cmd = ["yt-dlp", "--get-title", youtube_url]
    title_result = subprocess.run(
        title_cmd,
        check=True,
        capture_output=True,
        text=True
    )
    return title_result.stdout.strip()


def download_audio(youtube_url: str, output_dir: str) -> str:
    """
    Download YouTube audio using yt-dlp

    Args:
        youtube_url: YouTube video URL
        output_dir: Directory to save the audio file

    Returns:
        str: Path to downloaded audio file
    """
    logger.info(f"Downloading audio: {youtube_url}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    audio_path = os.path.join(output_dir, "audio.m4a")

    # Download audio only (best quality m4a/aac)
    cmd = [
        "yt-dlp",
        "--format", "ba[ext=m4a]/ba",
        "--output", audio_path,
        youtube_url
    ]

    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        # Verify file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info("Audio downloaded successfully")
        return audio_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download audio: {e.stderr}")
        raise Exception(f"Audio download failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Audio download error: {str(e)}")
        raise


def download_video(youtube_url: str, output_dir: str) -> str:
    """
    Download YouTube video (480p SD quality) using yt-dlp

    Args:
        youtube_url: YouTube video URL
        output_dir: Directory to save the video file

    Returns:
        str: Path to downloaded video file
    """
    logger.info(f"Downloading video (480p): {youtube_url}")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    video_path = os.path.join(output_dir, "video.mp4")

    # Download video at 480p quality (SD)
    cmd = [
        "yt-dlp",
        "--format", "best[height<=480]/best",
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

        # Verify file exists
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info("Video downloaded successfully")
        return video_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to download video: {e.stderr}")
        raise Exception(f"Video download failed: {e.stderr}")
    except Exception as e:
        logger.error(f"Video download error: {str(e)}")
        raise


def download_audio_and_video(youtube_url: str, output_dir: str) -> tuple[str, str, str]:
    """
    Download both audio and video from YouTube URL

    Args:
        youtube_url: YouTube video URL
        output_dir: Directory to save files

    Returns:
        tuple: (audio_path, video_path, video_title)
    """
    # Get title first
    title = get_video_title(youtube_url)
    logger.info(f"Downloading: {title}")

    # Download audio and video
    audio_path = download_audio(youtube_url, output_dir)
    video_path = download_video(youtube_url, output_dir)

    return audio_path, video_path, title
