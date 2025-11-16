"""Video frame extractor using FFmpeg"""
import os
import subprocess
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class VideoFrameExtractor:
    """Extract frames from video at specific timestamps using FFmpeg"""

    def __init__(self, video_path: str):
        """
        Initialize the frame extractor

        Args:
            video_path: Path to the video file
        """
        self.video_path = video_path

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        logger.info(f"Initialized VideoFrameExtractor with: {video_path}")

    def extract_frame(self, timestamp: float, output_path: str) -> str:
        """
        Extract a single frame from video at the specified timestamp

        Uses nearest keyframe for efficiency. FFmpeg will seek to the nearest
        keyframe before the timestamp and then extract the closest frame.

        Args:
            timestamp: Time in seconds to extract frame from
            output_path: Path where the extracted frame will be saved

        Returns:
            str: Path to the extracted frame
        """
        logger.info(f"Extracting frame at {timestamp:.2f}s -> {output_path}")

        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # FFmpeg command to extract a single frame
        # -ss: seek to timestamp (before input for faster seek to keyframe)
        # -i: input video file
        # -frames:v 1: extract only 1 frame
        # -q:v 2: JPEG quality (2 is high quality, similar to quality=85)
        # -y: overwrite output file if it exists
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),
            "-i", self.video_path,
            "-frames:v", "1",
            "-q:v", "2",
            "-y",
            output_path
        ]

        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )

            # Verify file was created
            if not os.path.exists(output_path):
                raise FileNotFoundError(f"Frame extraction failed: {output_path}")

            logger.debug(f"Frame extracted successfully: {output_path}")
            return output_path

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg frame extraction failed: {e.stderr}")
            raise Exception(f"Frame extraction failed at {timestamp}s: {e.stderr}")
        except Exception as e:
            logger.error(f"Frame extraction error: {str(e)}")
            raise

    def extract_frames_batch(self, timestamps: list[float], output_dir: str,
                            filename_pattern: str = "frame_{:04d}.jpg") -> list[str]:
        """
        Extract multiple frames from video at specified timestamps

        Args:
            timestamps: List of timestamps in seconds
            output_dir: Directory to save extracted frames
            filename_pattern: Pattern for output filenames (must include one format specifier)

        Returns:
            list[str]: Paths to all extracted frames
        """
        logger.info(f"Extracting {len(timestamps)} frames")

        os.makedirs(output_dir, exist_ok=True)

        frame_paths = []
        for i, timestamp in enumerate(timestamps):
            output_path = os.path.join(output_dir, filename_pattern.format(i))
            frame_path = self.extract_frame(timestamp, output_path)
            frame_paths.append(frame_path)

        logger.info(f"Extracted {len(frame_paths)} frames successfully")
        return frame_paths


def extract_frame_from_video(video_path: str, timestamp: float, output_path: str) -> str:
    """
    Convenience function to extract a single frame without creating an extractor object

    Args:
        video_path: Path to the video file
        timestamp: Time in seconds to extract frame from
        output_path: Path where the extracted frame will be saved

    Returns:
        str: Path to the extracted frame
    """
    extractor = VideoFrameExtractor(video_path)
    return extractor.extract_frame(timestamp, output_path)
