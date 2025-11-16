# Subs2SRS Anki Card Generator

A Python desktop application that converts MP4 videos into Anki flashcard decks using AssemblyAI transcription with word-level timestamps, creating subs2srs-style cards with screenshots and audio clips.

## Features

- **Simple Desktop App**: Streamlit-based UI runs locally in your browser
- **MP4 Video Upload**: Upload one or multiple MP4 files (up to 1GB each)
- **Deck Mode Options**:
  - **Combined Deck**: Merge all videos into a single deck
  - **Separate Decks**: Create individual decks per video
- **High-Quality Transcription**: Uses AssemblyAI for Japanese transcription with word-level timestamps
- **Speaker Diarization**: Automatically splits sentences based on speaker changes
- **Smart Segmentation**: Intelligently segments transcript into sentences
- **Media-Rich Cards**: Each card includes:
  - Screenshot extracted at sentence start time
  - Audio clip with 250ms padding
  - Japanese sentence text
- **Card Preview**: Preview cards before downloading
- **APKG Export**: Ready-to-import Anki deck package(s)
- **Dark Theme**: Modern dark UI for comfortable viewing

## Prerequisites

### Required Software

1. **Python 3.10+**
   ```bash
   python3 --version
   ```

2. **FFmpeg** (for audio and screenshot extraction)
   ```bash
   # macOS
   brew install ffmpeg

   # Linux (Ubuntu/Debian)
   sudo apt update && sudo apt install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **yt-dlp** (optional, for downloading YouTube videos)
   ```bash
   # macOS
   brew install yt-dlp

   # Linux
   sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
   sudo chmod a+rx /usr/local/bin/yt-dlp

   # Windows
   # Download from https://github.com/yt-dlp/yt-dlp/releases
   # Or: pip install yt-dlp
   ```

### API Keys

- **AssemblyAI API Key**: Sign up at [AssemblyAI](https://www.assemblyai.com/) to get a free API key

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd yt-subs2srs
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or with a virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running the Application

Simply run:

```bash
streamlit run app.py
```

The app will automatically open in your default web browser at `http://localhost:8501`

## Usage

### Step 1: Download YouTube Videos (Optional)

If you want to process YouTube videos, first download them as MP4 files using yt-dlp:

```bash
# Download at 360p resolution (recommended for file size)
yt-dlp -f "bestvideo[height<=360]+bestaudio/best[height<=360]" --merge-output-format mp4 "https://www.youtube.com/watch?v=VIDEO_ID"

# Or download best quality (larger file size)
yt-dlp --merge-output-format mp4 "https://www.youtube.com/watch?v=VIDEO_ID"

# Download playlist
yt-dlp -f "bestvideo[height<=360]+bestaudio/best[height<=360]" --merge-output-format mp4 "PLAYLIST_URL"
```

**Example** (Japanese content):
```bash
yt-dlp -f "bestvideo[height<=360]+bestaudio/best[height<=360]" --merge-output-format mp4 "https://www.youtube.com/watch?v=khRrXguNv3Q"
```

### Step 2: Generate Anki Cards

1. **Launch the App**: Run `streamlit run app.py`

2. **Upload MP4 Files**: Click "Browse files" and select one or more MP4 videos (up to 1GB each)

3. **Choose Deck Mode**:
   - **Combined Deck**: Merge all videos into one deck (sentences prefixed with filename)
   - **Separate Decks**: Create individual deck per video

4. **Enter AssemblyAI API Key**: Your API key (get one free at assemblyai.com)

5. **Generate Deck**: Click "Generate Deck" and wait for processing
   - Processing steps:
     - Saving uploaded file(s)
     - Extracting audio
     - Transcribing (this takes the longest, several minutes)
     - Segmenting into sentences
     - Generating cards with screenshots and audio
     - Creating deck(s)

6. **Preview Cards**: Once complete, preview cards with screenshots and audio

7. **Download APKG**: Click "Download APKG" to get your Anki deck(s)

8. **Import to Anki**: Open Anki and import the downloaded `.apkg` file(s)

## Card Format

Each Anki card contains:

- **Front**:
  - Audio clip (plays automatically)
  - Screenshot from video at sentence start time
- **Back**:
  - Same content as front
  - Japanese sentence text
  - (Optionally prefixed with [filename] in combined deck mode)

## Project Structure

```
yt-subs2srs/
├── app.py                      # Main Streamlit application
├── .streamlit/
│   └── config.toml             # Streamlit config (1GB upload, dark theme)
├── modules/
│   ├── audio_processor.py      # FFmpeg audio extraction
│   ├── transcriber.py          # AssemblyAI transcription
│   ├── segmenter.py            # Sentence segmentation
│   ├── video_frame_extractor.py # FFmpeg screenshot extraction
│   └── anki_deck.py            # genanki deck generation
├── tmp/                        # Temporary working directory
├── requirements.txt            # Python dependencies
└── README.md
```

## Configuration

### Sentence Segmentation

The application uses the following rules to segment sentences:

- **Speaker Changes**: Automatically splits when speaker changes
- **Punctuation**: Splits on Japanese sentence endings (。！？)
- **Length Limits**:
  - Minimum: 3 words
  - Maximum: 20 words
- **Japanese Character Filter**: Only includes sentences with Japanese characters

### Media Settings

- **Audio Format**: MP3, 128kbps, 44.1kHz, stereo
- **Screenshot Format**: JPEG, high quality (q:v 2, ~85%)
- **Screenshot Timing**: Extracted at sentence start_time
- **Audio Padding**: 250ms before and after each sentence
- **Upload Limit**: 1GB per file

## Troubleshooting

### "FFmpeg not found"
Install FFmpeg and verify it's in your PATH:
```bash
ffmpeg -version
```

### "File too large" error
The upload limit is 1GB per file. Compress your video if needed:
```bash
# Using yt-dlp to download at lower resolution
yt-dlp -f "bestvideo[height<=360]+bestaudio/best[height<=360]" --merge-output-format mp4 "VIDEO_URL"

# Or compress existing file with FFmpeg
ffmpeg -i input.mp4 -vf scale=640:360 -c:v libx264 -crf 28 -c:a aac -b:a 96k output.mp4
```

### "Transcription failed"
- Verify your AssemblyAI API key is correct
- Check if you have sufficient API credits
- Ensure the video has clear Japanese audio
- Try with a shorter video first

### "Screenshot extraction failed"
- Ensure FFmpeg is properly installed
- Check that the video file is not corrupted
- Verify the video has actual video frames (not audio-only)

### Port already in use
If port 8501 is already in use:
```bash
streamlit run app.py --server.port 8502
```

### yt-dlp download issues
- Make sure yt-dlp is up to date: `pip install --upgrade yt-dlp`
- Check if the video is available in your region
- Some videos may require authentication or may be blocked

## Packaging as Standalone Executable

You can package this as a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed app.py
```

Note: You'll need to include the modules folder and ensure FFmpeg and yt-dlp are accessible.

## Tech Stack

- **Streamlit** - Web UI framework
- **FFmpeg** - Audio extraction, screenshot extraction, and media processing
- **AssemblyAI** - Japanese transcription with word-level timestamps
- **genanki** - Anki deck generation
- **yt-dlp** (optional) - For downloading YouTube videos before processing

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [AssemblyAI](https://www.assemblyai.com/) for transcription services
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloads
- [FFmpeg](https://ffmpeg.org/) for media processing
- [genanki](https://github.com/kerrickstaley/genanki) for Anki deck generation
- [Streamlit](https://streamlit.io/) for the amazing UI framework

## Support

For issues and questions, please open an issue on GitHub.
