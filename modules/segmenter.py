"""Sentence segmentation"""
import re
import logging
from typing import List
from modules.transcriber import TranscriptWordData

logger = logging.getLogger(__name__)


class Sentence:
    """Sentence with timing and words"""
    def __init__(self, words: List[TranscriptWordData]):
        self.words = words
        self.text = "".join(w.text for w in words)
        self.start_time = words[0].start
        self.end_time = words[-1].end
        self.speaker = words[0].speaker


def segment_into_sentences(
    words: List[TranscriptWordData],
    max_length: int = 10,
    min_length: int = 3,
    max_duration: float = 8.0
) -> List[Sentence]:
    """
    Segment words into sentences

    Args:
        words: List of TranscriptWordData
        max_length: Maximum sentence length in words (default 10)
        min_length: Minimum sentence length in words (default 3)
        max_duration: Maximum sentence duration in seconds (default 8.0)

    Returns:
        list: List of Sentence objects
    """
    logger.info(f"Segmenting {len(words)} words into sentences...")

    if not words:
        return []

    sentences = []
    current_sentence = []
    current_speaker = words[0].speaker

    for i, word in enumerate(words):
        next_word = words[i + 1] if i + 1 < len(words) else None

        current_sentence.append(word)

        # Check if we should split
        should_split = False

        # Calculate duration
        if current_sentence:
            duration = word.end - current_sentence[0].start

        if not next_word:
            should_split = True  # End of transcript
        elif word.speaker != next_word.speaker:
            should_split = True  # Speaker change
        elif duration >= max_duration and len(current_sentence) >= min_length:
            should_split = True  # Exceeded max duration
        elif re.search(r'[。！？]', word.text) and len(current_sentence) >= 5:
            should_split = True  # Punctuation + reasonable length
        elif re.search(r'[、]', word.text) and len(current_sentence) >= 7:
            should_split = True  # Comma with decent length
        elif len(current_sentence) >= max_length:
            # Force split if too long, try to find natural pause
            if re.search(r'[。！？、\s]', word.text):
                should_split = True

        if should_split:
            # Create sentence if it meets criteria
            if len(current_sentence) >= min_length:
                sentences.append(Sentence(current_sentence))
            elif not next_word and current_sentence:
                # Include short final sentences
                sentences.append(Sentence(current_sentence))

            # Reset
            current_sentence = []
            if next_word:
                current_speaker = next_word.speaker

    logger.info(f"Created {len(sentences)} sentences")
    return sentences


def filter_valid_sentences(sentences: List[Sentence], min_length: int = 3) -> List[Sentence]:
    """
    Filter out invalid sentences

    Args:
        sentences: List of Sentence objects
        min_length: Minimum word count

    Returns:
        list: Filtered sentences
    """
    valid = []
    for sentence in sentences:
        # Must have minimum words
        if len(sentence.words) < min_length:
            continue

        # Must contain Japanese characters
        if not re.search(r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', sentence.text):
            continue

        valid.append(sentence)

    logger.info(f"Filtered to {len(valid)} valid sentences")
    return valid
