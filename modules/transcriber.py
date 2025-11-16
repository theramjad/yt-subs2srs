"""Transcription using AssemblyAI"""
import logging
import time
import requests

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
    Transcribe audio using AssemblyAI REST API

    Args:
        audio_path: Path to audio file
        api_key: AssemblyAI API key

    Returns:
        list: List of TranscriptWordData objects
    """
    logger.info("Starting transcription with AssemblyAI...")

    base_url = "https://api.assemblyai.com/v2"
    headers = {"authorization": api_key}

    # Step 1: Upload the audio file
    logger.info("Uploading audio file...")
    with open(audio_path, "rb") as f:
        upload_response = requests.post(
            f"{base_url}/upload",
            headers=headers,
            data=f
        )
    upload_response.raise_for_status()
    audio_url = upload_response.json()["upload_url"]
    logger.info(f"Audio uploaded: {audio_url}")

    # Step 2: Request transcription
    logger.info("Requesting transcription...")
    transcript_request = {
        "audio_url": audio_url,
        "language_code": "ja",  # Japanese
        "speaker_labels": True,  # Speaker diarization
        "punctuate": True,
        "format_text": True,
    }

    transcript_response = requests.post(
        f"{base_url}/transcript",
        json=transcript_request,
        headers=headers
    )
    transcript_response.raise_for_status()
    transcript_id = transcript_response.json()["id"]
    logger.info(f"Transcription job started: {transcript_id}")

    # Step 3: Poll for completion
    logger.info("Waiting for transcription to complete...")
    while True:
        status_response = requests.get(
            f"{base_url}/transcript/{transcript_id}",
            headers=headers
        )
        status_response.raise_for_status()
        transcript_data = status_response.json()

        status = transcript_data["status"]

        if status == "completed":
            logger.info("Transcription completed successfully")
            break
        elif status == "error":
            raise Exception(f"Transcription failed: {transcript_data.get('error')}")

        logger.info(f"Status: {status}... waiting")
        time.sleep(3)  # Wait 3 seconds before polling again

    # Extract words with timestamps
    words = []
    if transcript_data.get("words"):
        for word in transcript_data["words"]:
            words.append(TranscriptWordData(
                text=word["text"],
                start=word["start"] / 1000,  # Convert ms to seconds
                end=word["end"] / 1000,
                speaker=f"Speaker {word['speaker']}" if word.get("speaker") else None
            ))

    logger.info(f"Extracted {len(words)} words")
    return words
