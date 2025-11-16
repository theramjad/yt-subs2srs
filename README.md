# Subs2SRS Anki Card Generator

A web application that converts YouTube videos into Anki flashcard decks using AssemblyAI transcription with word-level timestamps, creating subs2srs-style cards with screenshots and audio clips.

## Features

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

## Tech Stack

### Frontend
- React with TypeScript
- Vite for build tooling
- Axios for API calls

### Backend
- NestJS
- AssemblyAI for transcription
- yt-dlp for video downloads
- FFmpeg for media processing
- genanki (Python) for Anki deck generation

## Prerequisites

### Required Software

1. **Node.js** (v18 or higher)
   ```bash
   node --version
   ```

2. **Python 3** (for genanki)
   ```bash
   python3 --version
   ```

3. **yt-dlp** (for YouTube downloads)
   ```bash
   # macOS
   brew install yt-dlp

   # Linux
   sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp
   sudo chmod a+rx /usr/local/bin/yt-dlp

   # Windows
   # Download from https://github.com/yt-dlp/yt-dlp/releases
   ```

4. **FFmpeg** (for media processing)
   ```bash
   # macOS
   brew install ffmpeg

   # Linux (Ubuntu/Debian)
   sudo apt update && sudo apt install ffmpeg

   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

5. **genanki** (Python library)
   ```bash
   pip3 install genanki
   ```

### API Keys

- **AssemblyAI API Key**: Sign up at [AssemblyAI](https://www.assemblyai.com/) to get a free API key

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd yt-subs2srs
```

### 2. Install Backend Dependencies

```bash
cd backend
npm install
```

### 3. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

### 4. Configure Proxy (Optional)

If you need to use a proxy for YouTube downloads:

```bash
cd ../backend
nano proxy.config.json
```

Edit the configuration:
```json
{
  "enabled": true,
  "url": "http://your-proxy:port",
  "type": "residential",
  "rotation": true
}
```

Recommended proxy providers: Bright Data, Oxylabs, SmartProxy

## Running the Application

### Development Mode

You need to run both frontend and backend servers.

#### Terminal 1 - Backend Server
```bash
cd backend
npm run start:dev
```

The backend will run on `http://localhost:3000`

#### Terminal 2 - Frontend Server
```bash
cd frontend
npm run dev
```

The frontend will run on `http://localhost:5173`

### Production Mode

#### Build Backend
```bash
cd backend
npm run build
npm start
```

#### Build Frontend
```bash
cd frontend
npm run build
npm run preview
```

## Usage

1. **Open the Application**: Navigate to `http://localhost:5173` in your browser

2. **Enter YouTube URL**: Paste the URL of the Japanese YouTube video you want to convert

3. **Enter AssemblyAI API Key**:
   - Your API key is stored in browser localStorage for convenience
   - It's only sent to your local backend server

4. **Generate Deck**: Click "Generate Deck" and wait for processing
   - Processing steps:
     - Downloading video (360p)
     - Extracting audio
     - Transcribing (this takes the longest, several minutes)
     - Segmenting into sentences
     - Generating cards
     - Creating deck

5. **Preview Cards**: Once complete, preview the first few cards

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
├── backend/
│   ├── src/
│   │   ├── modules/
│   │   │   ├── video/          # Video download service
│   │   │   ├── audio/          # Audio extraction service
│   │   │   ├── transcription/  # AssemblyAI service
│   │   │   ├── cards/          # Card generation services
│   │   │   └── processing/     # Main processing pipeline
│   │   ├── scripts/
│   │   │   └── generate_apkg.py # Python genanki script
│   │   ├── app.module.ts
│   │   └── main.ts
│   ├── proxy.config.json
│   ├── package.json
│   └── tsconfig.json
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   │   └── api.ts         # API client
│   │   ├── App.tsx            # Main app component
│   │   ├── App.css
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.ts
├── plan.md
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

### "genanki module not found"
Install genanki:
```bash
pip3 install genanki
python3 -c "import genanki"
```

### "YouTube download failed"
- Check if the video is available in your region
- Try enabling proxy in `proxy.config.json`
- Verify the YouTube URL is correct

### "Transcription failed"
- Verify your AssemblyAI API key is correct
- Check if you have sufficient API credits
- Ensure the video has clear Japanese audio

### Backend won't start
```bash
cd backend
rm -rf node_modules package-lock.json
npm install
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## API Endpoints

- `POST /api/process` - Start processing a video
- `GET /api/status/:jobId` - Get processing status
- `GET /api/preview/:jobId` - Get card preview
- `GET /api/download/:jobId` - Download APKG file
- `GET /api/health` - Health check

## Development

### Backend Development
```bash
cd backend
npm run start:dev  # Auto-reload on changes
```

### Frontend Development
```bash
cd frontend
npm run dev  # Hot module replacement
```

### Linting
```bash
# Backend
cd backend
npm run lint

# Frontend
cd frontend
npm run lint
```

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- [AssemblyAI](https://www.assemblyai.com/) for transcription services
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloads
- [FFmpeg](https://ffmpeg.org/) for media processing
- [genanki](https://github.com/kerrickstaley/genanki) for Anki deck generation

## Support

For issues and questions, please open an issue on GitHub.
