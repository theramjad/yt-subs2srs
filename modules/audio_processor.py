"""Audio processing using FFmpeg"""
import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def extract_audio(video_path: str, output_dir: str) -> str:
    """
    Extract audio from video as MP3

    Args:
        video_path: Path to video file
        output_dir: Directory to save audio

    Returns:
        str: Path to extracted audio file
    """
    logger.info(f"Extracting audio from: {video_path}")

    audio_path = os.path.join(output_dir, "audio.mp3")

    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-vn",  # No video
        "-ar", "44100",  # Sample rate
        "-ac", "2",  # Stereo
        "-b:a", "128k",  # Bitrate
        "-y",  # Overwrite
        audio_path
    ]

    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        logger.info("Audio extracted successfully")

        # Delete video to save space
        os.remove(video_path)
        logger.info("Video file deleted")

        return audio_path

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to extract audio: {e.stderr}")
        raise Exception(f"Audio extraction failed: {e.stderr}")


def extract_audio_clip(
    audio_path: str,
    start_time: float,
    end_time: float,
    output_path: str,
    padding: float = 0.25
) -> None:
    """
    Extract audio clip with padding

    Args:
        audio_path: Source audio file
        start_time: Start time in seconds
        end_time: End time in seconds
        output_path: Output file path
        padding: Padding in seconds (default 0.25s)
    """
    padded_start = max(0, start_time - padding)
    padded_end = end_time + padding
    duration = padded_end - padded_start

    cmd = [
        "ffmpeg",
        "-ss", str(padded_start),
        "-i", audio_path,
        "-t", str(duration),
        "-c", "copy",
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
    except subprocess.CalledProcessError:
        # If copy fails, try re-encoding
        cmd = [
            "ffmpeg",
            "-ss", str(padded_start),
            "-i", audio_path,
            "-t", str(duration),
            "-b:a", "128k",
            "-y",
            output_path
        ]
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

    logger.info(f"Audio clip extracted: {output_path}")
