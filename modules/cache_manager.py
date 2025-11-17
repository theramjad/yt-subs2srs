"""Cache manager for transcriptions and media files"""
import os
import json
import time
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional
from modules.transcriber import TranscriptWordData

logger = logging.getLogger(__name__)


class CacheManager:
    """Manages transcript and media caching for regeneration"""

    def __init__(self, session_dir: Path):
        """
        Initialize cache manager for a session

        Args:
            session_dir: Path to session directory (e.g., tmp/{session_id})
        """
        self.session_dir = Path(session_dir)
        self.cache_file = self.session_dir / "transcript_cache.json"
        self.activity_file = self.session_dir / "last_activity.txt"
        self.source_dir = self.session_dir / "source"

        # Create directories
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.source_dir.mkdir(exist_ok=True)

        # Update activity timestamp
        self.update_activity()

    def update_activity(self):
        """Update last activity timestamp"""
        with open(self.activity_file, 'w') as f:
            f.write(str(time.time()))

    def save_transcript(self, video_name: str, words: List[TranscriptWordData],
                       video_path: str, audio_path: str):
        """
        Save transcript to cache

        Args:
            video_name: Name of the video (without extension)
            words: List of TranscriptWordData objects
            video_path: Path to video file
            audio_path: Path to audio file
        """
        # Load existing cache or create new
        cache = self.load_cache()

        # Convert TranscriptWordData to serializable dict
        words_dict = [
            {
                'text': w.text,
                'start': w.start,
                'end': w.end,
                'speaker': w.speaker
            }
            for w in words
        ]

        # Store in cache
        cache[video_name] = {
            'words': words_dict,
            'video_path': video_path,
            'audio_path': audio_path,
            'timestamp': time.time()
        }

        # Save cache
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

        logger.info(f"Cached transcript for {video_name} ({len(words)} words)")
        self.update_activity()

    def load_cache(self) -> Dict:
        """Load cache from file"""
        if self.cache_file.exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}

    def get_transcript(self, video_name: str) -> Optional[Dict]:
        """
        Get cached transcript for a video

        Args:
            video_name: Name of the video

        Returns:
            Dict with 'words', 'video_path', 'audio_path' or None if not cached
        """
        cache = self.load_cache()
        if video_name in cache:
            logger.info(f"Using cached transcript for {video_name}")
            self.update_activity()
            return cache[video_name]
        return None

    def has_transcript(self, video_name: str) -> bool:
        """Check if transcript is cached for a video"""
        cache = self.load_cache()
        return video_name in cache

    def words_to_objects(self, words_dict: List[Dict]) -> List[TranscriptWordData]:
        """Convert dict words back to TranscriptWordData objects"""
        return [
            TranscriptWordData(
                text=w['text'],
                start=w['start'],
                end=w['end'],
                speaker=w['speaker']
            )
            for w in words_dict
        ]

    def get_age_hours(self) -> float:
        """Get age of session in hours based on last activity"""
        if not self.activity_file.exists():
            return 0.0

        with open(self.activity_file, 'r') as f:
            last_activity = float(f.read().strip())

        age_seconds = time.time() - last_activity
        return age_seconds / 3600  # Convert to hours

    def cleanup(self):
        """Delete entire session directory"""
        if self.session_dir.exists():
            shutil.rmtree(self.session_dir)
            logger.info(f"Cleaned up session directory: {self.session_dir}")


def cleanup_old_sessions(tmp_dir: Path = Path("tmp"), max_age_hours: float = 1.0):
    """
    Clean up old session directories

    Args:
        tmp_dir: Path to tmp directory containing session folders
        max_age_hours: Maximum age in hours before cleanup (default 1.0)
    """
    if not tmp_dir.exists():
        return

    cleaned = 0
    for session_dir in tmp_dir.iterdir():
        if not session_dir.is_dir():
            continue

        try:
            cache_mgr = CacheManager(session_dir)
            age = cache_mgr.get_age_hours()

            if age > max_age_hours:
                cache_mgr.cleanup()
                cleaned += 1
                logger.info(f"Cleaned up session {session_dir.name} (age: {age:.2f}h)")
        except Exception as e:
            logger.error(f"Error cleaning up {session_dir}: {e}")

    if cleaned > 0:
        logger.info(f"Cleaned up {cleaned} old session(s)")
