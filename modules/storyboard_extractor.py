"""Extract thumbnails from YouTube storyboards"""
import os
import subprocess
import logging
import json
import re
from pathlib import Path
from PIL import Image
import io
import base64

logger = logging.getLogger(__name__)


class StoryboardExtractor:
    """Extract individual thumbnails from YouTube storyboard"""

    def __init__(self, youtube_url: str, output_dir: str):
        """
        Initialize storyboard extractor

        Args:
            youtube_url: YouTube video URL
            output_dir: Directory to save storyboard files
        """
        self.youtube_url = youtube_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.storyboard_path = None
        self.metadata = None

    def download_storyboard(self) -> None:
        """Download storyboard (sb0 format - 320x180)"""
        logger.info("Downloading storyboard...")

        # Get metadata
        metadata_cmd = ["yt-dlp", "-j", self.youtube_url]
        result = subprocess.run(
            metadata_cmd,
            check=True,
            capture_output=True,
            text=True
        )

        data = json.loads(result.stdout)
        sb_formats = [f for f in data.get('formats', []) if f.get('format_id') == 'sb0']

        if not sb_formats:
            raise Exception("No storyboard format available")

        self.metadata = sb_formats[0]

        # Download storyboard
        self.storyboard_path = self.output_dir / "storyboard.mhtml"
        download_cmd = [
            "yt-dlp",
            "-f", "sb0",
            "-o", str(self.storyboard_path),
            self.youtube_url
        ]

        subprocess.run(
            download_cmd,
            check=True,
            capture_output=True,
            text=True
        )

        logger.info(f"Storyboard downloaded: {self.storyboard_path}")

    def extract_thumbnail(self, timestamp: float, output_path: str) -> None:
        """
        Extract thumbnail nearest to timestamp

        Args:
            timestamp: Time in seconds
            output_path: Output image path
        """
        if not self.metadata or not self.storyboard_path:
            raise Exception("Storyboard not downloaded. Call download_storyboard() first.")

        # Calculate thumbnail parameters
        fps = self.metadata['fps']
        interval = 1.0 / fps  # Seconds per thumbnail
        rows = self.metadata['rows']
        cols = self.metadata['columns']
        thumb_width = self.metadata['width']
        thumb_height = self.metadata['height']

        # Find nearest thumbnail index
        thumb_index = int(round(timestamp / interval))

        # Parse MHTML and extract images
        with open(self.storyboard_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Find all base64 image data
        pattern = r'Content-Type: image/jpeg\s+Content-Transfer-Encoding: base64\s+Content-Location: ([^\s]+)\s+([A-Za-z0-9+/=\s]+)'
        matches = re.findall(pattern, content, re.MULTILINE)

        if not matches:
            raise Exception("No images found in storyboard")

        # Calculate which fragment and position
        thumbs_per_fragment = rows * cols
        fragment_index = thumb_index // thumbs_per_fragment
        position_in_fragment = thumb_index % thumbs_per_fragment

        if fragment_index >= len(matches):
            fragment_index = len(matches) - 1
            position_in_fragment = thumbs_per_fragment - 1

        # Extract the grid image
        _, base64_data = matches[fragment_index]
        base64_data = base64_data.replace('\n', '').replace(' ', '')
        image_data = base64.b64decode(base64_data)
        grid_image = Image.open(io.BytesIO(image_data))

        # Calculate position in grid
        row = position_in_fragment // cols
        col = position_in_fragment % cols

        # Extract specific thumbnail
        left = col * thumb_width
        top = row * thumb_height
        right = left + thumb_width
        bottom = top + thumb_height

        thumbnail = grid_image.crop((left, top, right, bottom))

        # Save thumbnail
        thumbnail.save(output_path, quality=85)
        logger.info(f"Thumbnail extracted: {output_path} (at {timestamp:.2f}s, nearest frame at {thumb_index * interval:.2f}s)")


def download_and_setup_storyboard(youtube_url: str, output_dir: str) -> StoryboardExtractor:
    """
    Download storyboard and return extractor

    Args:
        youtube_url: YouTube video URL
        output_dir: Directory to save files

    Returns:
        StoryboardExtractor instance ready to extract thumbnails
    """
    extractor = StoryboardExtractor(youtube_url, output_dir)
    extractor.download_storyboard()
    return extractor
