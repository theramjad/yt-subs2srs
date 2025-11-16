# Subs2SRS Anki Card Generator - Implementation Plan

## Project Overview
A web application that converts YouTube videos into Anki flashcard decks using AssemblyAI transcription with word-level timestamps, creating subs2srs-style cards with screenshots and audio clips.

## Tech Stack
- **Frontend**: React
- **Backend**: NestJS
- **Video Download**: yt-dlp (with proxy support)
- **Audio Extraction**: FFmpeg
- **Transcription**: AssemblyAI API
- **Screenshot Extraction**: FFmpeg
- **Anki Deck Generation**: genanki (Python) or Node.js alternative
- **Storage**: Local filesystem (temporary, auto-cleanup)

## Architecture

### Frontend (React)
**Single Page with:**
- YouTube URL input field
- AssemblyAI API key input field (stored in localStorage)
- "Generate Deck" button
- Progress indicator showing:
  - Downloading video (360p)
  - Extracting audio
  - Transcribing (polling status)
  - Generating cards
  - Creating deck
- Card preview section (before download)
- Download APKG button
- Inline error messages

### Backend (NestJS)

#### API Endpoints:
1. `POST /api/process` - Start processing
   - Body: `{ youtubeUrl, assemblyAiApiKey }`
   - Returns: `{ jobId, status }`

2. `GET /api/status/:jobId` - Poll processing status
   - Returns: `{ status, progress, currentStep, error? }`

3. `GET /api/preview/:jobId` - Preview generated cards
   - Returns: Array of cards with base64 images/audio

4. `GET /api/download/:jobId` - Download APKG file
   - Returns: APKG file, then deletes temp files

#### Processing Pipeline:

**Step 1: Video Download (360p)**
- Use yt-dlp with proxy configuration from `proxy.config.json`
- Format: `--format "best[height<=360]"`
- Save to `/tmp/{jobId}/video.mp4`
- Proxy config: `--proxy "http://proxy:port"` (residential/rotating recommended)

**Step 2: Audio Extraction**
- FFmpeg: Extract MP3 at 128kbps
- Command: `ffmpeg -i video.mp4 -vn -ar 44100 -ac 2 -b:a 128k audio.mp3`
- Delete video.mp4 after extraction

**Step 3: AssemblyAI Transcription**
- Upload audio to AssemblyAI
- Config:
  ```json
  {
    "language_code": "ja",
    "speaker_labels": true,
    "punctuate": true,
    "format_text": true
  }
  ```
- Poll status every 5 seconds until complete
- Retrieve word-level timestamps

**Step 4: Sentence Segmentation**
- Split into sentences based on:
  - Speaker changes (check `speaker` field)
  - Punctuation marks (。！？)
  - Long sentences (>15-20 words)
- Each sentence stores:
  - Text
  - Start time (first word start)
  - End time (last word end)
  - Speaker ID

**Step 5: Screenshot Extraction**
- For each sentence, extract screenshot at first word's start time
- FFmpeg command: `ffmpeg -ss {startTime} -i video.mp4 -frames:v 1 -q:v 2 -s 640x360 screenshot_{index}.webp`
- Format: WebP, 360p resolution

**Step 6: Audio Clip Extraction**
- For each sentence:
  - Add 250ms padding: `start - 0.25s` to `end + 0.25s`
  - FFmpeg: `ffmpeg -i audio.mp3 -ss {start-0.25} -to {end+0.25} -c copy clip_{index}.mp3`

**Step 7: APKG Generation**
- Use genanki (via Python subprocess) or `anki-apkg-export` (npm)
- Card template:
  - **Front**: `[sound:clip_{index}.mp3]<br><img src="screenshot_{index}.webp">`
  - **Back**: `{{Front}}<hr id="answer">{sentence_text}`
- Model fields: `["Audio", "Image", "Sentence"]`
- Deck name: Video title (from yt-dlp metadata)
- Include all media files in package
- Output: `{videoTitle}.apkg`

**Step 8: Cleanup**
- After user downloads APKG:
  - Delete `/tmp/{jobId}/` directory
  - Remove job from memory (no persistence)

## File Structure
```
subs2srs-anki/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UrlInput.tsx
│   │   │   ├── ApiKeyInput.tsx
│   │   │   ├── ProgressIndicator.tsx
│   │   │   ├── CardPreview.tsx
│   │   │   └── ErrorDisplay.tsx
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
├── backend/
│   ├── src/
│   │   ├── modules/
│   │   │   ├── video/
│   │   │   │   ├── video.service.ts (yt-dlp)
│   │   │   │   └── video.controller.ts
│   │   │   ├── audio/
│   │   │   │   └── audio.service.ts (FFmpeg)
│   │   │   ├── transcription/
│   │   │   │   └── assemblyai.service.ts
│   │   │   ├── cards/
│   │   │   │   ├── segmentation.service.ts
│   │   │   │   ├── screenshot.service.ts
│   │   │   │   └── anki.service.ts
│   │   │   └── processing/
│   │   │       ├── processing.controller.ts
│   │   │       └── processing.service.ts
│   │   ├── app.module.ts
│   │   └── main.ts
│   ├── scripts/
│   │   └── generate_apkg.py (genanki)
│   ├── proxy.config.json
│   └── package.json
├── docker-compose.yml (optional)
└── README.md
```

## Key Implementation Details

### Proxy Configuration (`proxy.config.json`)
```json
{
  "enabled": true,
  "url": "http://proxy-provider:port",
  "type": "residential",
  "rotation": true
}
```
**Recommended providers**: Bright Data, Oxylabs, SmartProxy (rotating residential)

### Sentence Boundary Logic
```typescript
function shouldSplitSentence(currentWord, nextWord, wordsSinceLastSplit) {
  // Speaker change
  if (currentWord.speaker !== nextWord.speaker) return true;

  // Punctuation + long sentence
  if (currentWord.text.match(/[。！？]/) && wordsSinceLastSplit > 15) return true;

  return false;
}
```

### Progress Updates
Store job state in memory:
```typescript
{
  jobId: string,
  status: 'downloading' | 'extracting' | 'transcribing' | 'generating' | 'complete',
  progress: number, // 0-100
  error?: string
}
```

## Testing Checklist
- [ ] YouTube video downloads at 360p
- [ ] Proxy configuration works
- [ ] Audio extracted as MP3 128kbps
- [ ] AssemblyAI returns word-level timestamps
- [ ] Sentences split correctly on speaker changes
- [ ] Sentences split on punctuation
- [ ] Screenshots captured at sentence start
- [ ] Audio clips have 250ms padding
- [ ] APKG file opens in Anki
- [ ] Cards show screenshot + audio on front
- [ ] Cards show sentence text on back
- [ ] Files deleted after download

## Development Phases
1. **Phase 1**: Backend video download + audio extraction
2. **Phase 2**: AssemblyAI integration + polling
3. **Phase 3**: Sentence segmentation logic
4. **Phase 4**: Screenshot + audio clip extraction
5. **Phase 5**: APKG generation with genanki
6. **Phase 6**: Frontend React UI
7. **Phase 7**: Integration + testing
8. **Phase 8**: File cleanup + error handling

## User Requirements Summary
- **Video Quality**: 360p
- **Audio Format**: MP3, 128kbps (normal quality)
- **Language**: Japanese (hardcoded)
- **Proxies**: Manual configuration in proxy.config.json
- **Speaker Diarization**: Enabled
- **API Key Storage**: Browser localStorage
- **Transcription Polling**: Check status every 5 seconds
- **Screenshot Timing**: Start of sentence (first word)
- **Screenshot Format**: WebP, 360p resolution
- **Card Granularity**: One sentence per card
- **Audio Padding**: 250ms before/after sentence
- **Card Front**: Screenshot + Audio
- **Card Back**: Japanese sentence text
- **No Translation**: Leave translation fields empty
- **Deck Name**: Video title
- **Output Format**: APKG (packaged Anki deck)
- **Processing**: One URL at a time
- **Preview**: Show cards before download
- **No Database**: Stateless, files deleted after download
- **No Rate Limiting**: For initial version
