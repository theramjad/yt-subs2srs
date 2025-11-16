"""Transcription using AssemblyAI"""
import logging
from assemblyai import AssemblyAI, TranscriptWord

logger = logging.getLogger(__name__)


class TranscriptWordData:
    """Word with timestamp and speaker info"""
    def __init__(self, text: str, start: float, end: float, speaker: str = None):
        self.text = text
        self.start = start  # in seconds
        self.end = end  # in seconds
        self.speaker = speaker


def transcribe_audio(audio_path: str, api_key: str) -> list[TranscriptWordData]:
    """
    Transcribe audio using AssemblyAI

    Args:
        audio_path: Path to audio file
        api_key: AssemblyAI API key

    Returns:
        list: List of TranscriptWordData objects
    """
    logger.info("Starting transcription with AssemblyAI...")

    client = AssemblyAI(api_key=api_key)

    # Configure transcription
    config = {
        "audio": audio_path,
        "language_code": "ja",  # Japanese
        "speaker_labels": True,  # Speaker diarization
        "punctuate": True,
        "format_text": True,
    }

    # Transcribe
    transcript = client.transcripts.transcribe(**config)

    if transcript.status == "error":
        raise Exception(f"Transcription failed: {transcript.error}")

    logger.info("Transcription completed successfully")

    # Extract words with timestamps
    words = []
    if transcript.words:
        for word in transcript.words:
            words.append(TranscriptWordData(
                text=word.text,
                start=word.start / 1000,  # Convert ms to seconds
                end=word.end / 1000,
                speaker=f"Speaker {word.speaker}" if word.speaker else None
            ))

    logger.info(f"Extracted {len(words)} words")
    return words
