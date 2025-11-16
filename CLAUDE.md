# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Subs2SRS Anki Card Generator - A Streamlit web app that converts YouTube videos into Anki flashcard decks with audio clips and Japanese sentence text. Currently **audio-only** (screenshots/video temporarily disabled).

## Running the Application

```bash
# Development
source venv/bin/activate
streamlit run app.py
```

The app runs at http://localhost:8501 and auto-reloads on code changes.

**Cache clearing**: If code changes don't appear, Python modules may be cached:
```bash
pkill -f streamlit
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
source venv/bin/activate && streamlit run app.py
```

## System Dependencies

Required external tools (must be installed on system, not in venv):
- **yt-dlp**: YouTube video/audio downloads
- **ffmpeg**: Audio extraction and clipping

Verify installation:
```bash
yt-dlp --version
ffmpeg -version
```

## Architecture

### Pipeline Flow

```
YouTube URL → Audio Download → Transcription → Segmentation → Card Generation → APKG Export
```

**Entry point**: `app.py` orchestrates the pipeline via `process_video()` function

### Module Responsibilities

**`app.py`** (Streamlit UI orchestration):
- Session state management: `processing`, `completed`, `apkg_path`, `preview_cards`
- Progress tracking with visual feedback
- `process_video()` orchestrates the entire pipeline at app.py:56

**`modules/video_downloader.py`** (yt-dlp wrapper):
- `get_video_title(url)` → title string for deck naming
- `download_audio(url, output_dir)` → audio file path (m4a format)
- `download_thumbnail(url, output_dir)` → thumbnail image path (jpg/webp/png)
- Format selector for audio: `"ba[ext=m4a]/ba"` (best audio)
- `download_video()` exists but is not currently used (full video download disabled)

**`modules/audio_processor.py`** (FFmpeg wrapper):
- `extract_audio(m4a_path, output_dir)` → WAV/MP3 file for transcription
- `extract_audio_clip(audio, start, end, output, padding=0.25)` → sentence MP3 clips
- Clips use 250ms padding before/after for natural listening

**`modules/transcriber.py`** (AssemblyAI REST API):
- `transcribe_audio(audio_path, api_key)` → List[TranscriptWordData]
- REST workflow: upload file → submit job → poll status (3s interval) → extract words
- Language code: `"ja"` (Japanese) with `speaker_labels=True`, `punctuate=True`
- **Critical timing data**: Word timestamps in milliseconds, converted to seconds (÷1000)

**`modules/segmenter.py`** (sentence boundary detection):
- `segment_into_sentences(words, max_length=10, min_length=3, max_duration=8.0)` → List[Sentence]
- Split triggers (in priority order):
  1. Speaker changes (from transcription labels)
  2. Japanese punctuation (。！？) + min 5 words
  3. Max duration exceeded (8s) + min 3 words
  4. Japanese comma (、) + 7 words
  5. Max length (10 words)
- `filter_valid_sentences(sentences, min_length=3)` → filters non-Japanese and short sentences

**`modules/anki_deck.py`** (genanki wrapper):
- `create_anki_deck(cards, deck_name, output_path)` → APKG file path
- Card format: `{audioFile: str, imageFile: str, sentence: str}`
- `imageFile` contains the YouTube thumbnail path (same for all cards in deck)
- Model: "Subs2SRS Japanese" with front (audio+image) and back (+ sentence text)

### Key Data Structures

```python
# 1. Transcription output (modules/transcriber.py:9)
class TranscriptWordData:
    text: str       # Word text
    start: float    # Start time in seconds (converted from ms)
    end: float      # End time in seconds (converted from ms)
    speaker: str    # "Speaker A", "Speaker B", etc.

# 2. Segmentation output (modules/segmenter.py:10)
class Sentence:
    words: List[TranscriptWordData]  # Source words
    text: str                        # Concatenated text (no spaces)
    start_time: float                # First word start
    end_time: float                  # Last word end
    speaker: str                     # First word speaker

# 3. Card format (passed to anki_deck.py:46)
card = {
    'audioFile': str,      # Path to sentence MP3 clip
    'imageFile': str,      # Path to YouTube thumbnail (shared across all cards)
    'sentence': str        # Japanese text
}
```

### Timing Precision

AssemblyAI returns timestamps in **milliseconds**, which are converted to **seconds** at transcriber.py:92-93. All downstream modules (segmenter, audio_processor) expect seconds as floats.

### Working Directory

- `tmp/current/` - All processing artifacts (auto-created at app.py:60)
- Cleaned up via "Create Another Deck" button (app.py:226)
- Audio/video source files deleted after clip extraction (app.py:121-124)
- **Do not commit** `tmp/` directory

## Current State: Thumbnail Mode

Cards now contain:
- ✅ Audio clips (sentence-level with 250ms padding)
- ✅ Japanese text
- ✅ YouTube thumbnail (same thumbnail used for all cards in a deck)

**Note**: Using YouTube thumbnails instead of per-sentence screenshots simplifies implementation and avoids yt-dlp format selection issues. All cards from the same video share the same thumbnail image.

Video frame extraction modules exist but are not used:
- `modules/video_frame_extractor.py` (not used)
- `modules/screenshot.py` (not used)

## Development Workflow

### Git Commits

**Auto-commit after significant changes**: When making substantial code changes (new features, bug fixes, refactoring), automatically create commits without asking the user first. Use descriptive commit messages that explain what was changed and why.

Example commit workflow:
```bash
git add -A
git commit -m "Add thumbnail support for Anki cards

Uses yt-dlp to download video thumbnails instead of extracting
frames, simplifying video handling and avoiding format issues."
```

## Important Technical Details

### yt-dlp Commands
- **Audio download**: `yt-dlp --format "ba[ext=m4a]/ba" --output <path> <url>`
- **Thumbnail download**: `yt-dlp --write-thumbnail --skip-download --convert-thumbnails jpg --output <path> <url>`
- **Get title**: `yt-dlp --get-title <url>`

### AssemblyAI Configuration
- Language: `"ja"` (Japanese)
- Features: `speaker_labels=True`, `punctuate=True`, `format_text=True`
- Polling: 3 seconds until status == "completed"
- **API key**: Users provide via UI - never hardcode or commit

### Sentence Segmentation Tuning
Parameters optimized for Japanese language learning (see segmenter.py:20-24):
- `max_length`: 10 words
- `min_length`: 3 words
- `max_duration`: 8.0 seconds
- `padding`: 0.25 seconds (250ms) before/after audio clips

### Streamlit Session State
- `processing`: bool - prevents duplicate form submissions
- `completed`: bool - triggers results display
- `apkg_path`: str - path to generated deck file
- `preview_cards`: list - cards to display in UI
