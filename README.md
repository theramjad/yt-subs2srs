# Subs2SRS Anki Card Generator

A Python desktop application that converts YouTube videos into Anki flashcard decks using AssemblyAI transcription with word-level timestamps, creating subs2srs-style cards with screenshots and audio clips.

## Features

- **Simple Desktop App**: Streamlit-based UI runs locally in your browser
- **YouTube Video Processing**: Downloads videos at 360p resolution
- **High-Quality Transcription**: Uses AssemblyAI for Japanese transcription with word-level timestamps
- **Speaker Diarization**: Automatically splits sentences based on speaker changes
- **Smart Segmentation**: Intelligently segments transcript into sentences
- **Media-Rich Cards**: Each card includes:
  - Screenshot from the video (at sentence start)
  - Audio clip with 250ms padding
  - Japanese sentence text
- **Card Preview**: Preview cards before downloading
- **APKG Export**: Ready-to-import Anki deck package

## Prerequisites

### Required Software

1. **Python 3.10+**
   ```bash
   python3 --version
   ```

2. **yt-dlp** (for YouTube downloads)
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

3. **FFmpeg** (for media processing)
   ```bash
   # macOS
   brew install ffmpeg

   # Linux (Ubuntu/Debian)
   sudo apt update && sudo apt install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
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

1. **Launch the App**: Run `streamlit run app.py`

2. **Enter YouTube URL**: Paste the URL of the Japanese YouTube video you want to convert

3. **Enter AssemblyAI API Key**: Your API key (get one free at assemblyai.com)

4. **Generate Deck**: Click the "Generate Deck" button and wait for processing
   - Processing steps:
     - Downloading video (360p)
     - Extracting audio
     - Transcribing (this takes the longest, several minutes)
     - Segmenting into sentences
     - Generating cards
     - Creating deck

5. **Preview Cards**: Once complete, preview the first 3 cards

6. **Download APKG**: Click "Download APKG" to get your Anki deck

7. **Import to Anki**: Open Anki and import the downloaded `.apkg` file

## Card Format

Each Anki card contains:

- **Front**:
  - Audio clip (plays automatically)
  - Screenshot from video
- **Back**:
  - Same content as front
  - Japanese sentence text

## Project Structure

```
yt-subs2srs/
├── app.py                      # Main Streamlit application
├── modules/
│   ├── video_downloader.py     # yt-dlp video downloads
│   ├── audio_processor.py      # FFmpeg audio extraction
│   ├── transcriber.py          # AssemblyAI transcription
│   ├── segmenter.py            # Sentence segmentation
│   ├── screenshot.py           # Screenshot extraction
│   └── anki_deck.py            # genanki deck generation
├── tmp/                        # Temporary working directory
├── requirements.txt            # Python dependencies
├── plan.md                     # Original implementation plan
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

- **Video Quality**: 360p
- **Audio Format**: MP3, 128kbps, 44.1kHz, stereo
- **Screenshot Format**: WebP, 640x360 resolution
- **Audio Padding**: 250ms before and after each sentence

## Troubleshooting

### "yt-dlp not found"
Make sure yt-dlp is installed and in your PATH:
```bash
yt-dlp --version
```

### "FFmpeg not found"
Install FFmpeg:
```bash
ffmpeg -version
```

### "YouTube download failed"
- Check if the video is available in your region
- Verify the YouTube URL is correct
- Make sure yt-dlp is up to date: `pip install --upgrade yt-dlp`

### "Transcription failed"
- Verify your AssemblyAI API key is correct
- Check if you have sufficient API credits
- Ensure the video has clear Japanese audio

### Port already in use
If port 8501 is already in use:
```bash
streamlit run app.py --server.port 8502
```

## Packaging as Standalone Executable

You can package this as a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed app.py
```

Note: You'll need to include the modules folder and ensure FFmpeg and yt-dlp are accessible.

## Tech Stack

- **Streamlit** - Web UI framework
- **yt-dlp** - YouTube video downloads
- **FFmpeg** - Media processing
- **AssemblyAI** - Japanese transcription with word-level timestamps
- **genanki** - Anki deck generation

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
