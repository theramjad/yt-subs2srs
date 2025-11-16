import { Injectable, Logger } from '@nestjs/common';
import { AssemblyAI, Transcript, Word } from 'assemblyai';
import * as fs from 'fs';

export interface TranscriptWord {
  text: string;
  start: number; // in seconds
  end: number; // in seconds
  speaker?: string;
}

@Injectable()
export class AssemblyAIService {
  private readonly logger = new Logger(AssemblyAIService.name);

  /**
   * Transcribes audio file using AssemblyAI with word-level timestamps
   * @param audioPath - Path to the audio file
   * @param apiKey - AssemblyAI API key
   * @returns Array of words with timestamps and speaker labels
   */
  async transcribeAudio(
    audioPath: string,
    apiKey: string,
  ): Promise<TranscriptWord[]> {
    this.logger.log('Starting AssemblyAI transcription...');

    const client = new AssemblyAI({
      apiKey: apiKey,
    });

    try {
      // Read the audio file
      const audioFile = fs.createReadStream(audioPath);

      // Upload and transcribe with configuration
      const transcript = await client.transcripts.transcribe({
        audio: audioFile,
        language_code: 'ja', // Japanese
        speaker_labels: true, // Enable speaker diarization
        punctuate: true,
        format_text: true,
      });

      if (transcript.status === 'error') {
        throw new Error(`Transcription failed: ${transcript.error}`);
      }

      this.logger.log('Transcription completed successfully');

      // Extract word-level timestamps
      const words = this.extractWords(transcript);
      this.logger.log(`Extracted ${words.length} words with timestamps`);

      return words;
    } catch (error) {
      this.logger.error(`AssemblyAI transcription failed: ${error.message}`);
      throw new Error(`Transcription failed: ${error.message}`);
    }
  }

  /**
   * Extracts word-level data from AssemblyAI transcript
   */
  private extractWords(transcript: Transcript): TranscriptWord[] {
    if (!transcript.words || transcript.words.length === 0) {
      throw new Error('No words found in transcript');
    }

    return transcript.words.map((word: Word) => ({
      text: word.text,
      start: word.start / 1000, // Convert milliseconds to seconds
      end: word.end / 1000,
      speaker: word.speaker ? `Speaker ${word.speaker}` : undefined,
    }));
  }

  /**
   * Polls AssemblyAI for transcription status
   * This is a helper method for manual polling if needed
   */
  async pollTranscriptionStatus(
    transcriptId: string,
    apiKey: string,
  ): Promise<Transcript> {
    const client = new AssemblyAI({ apiKey });

    while (true) {
      const transcript = await client.transcripts.get(transcriptId);

      if (transcript.status === 'completed') {
        return transcript;
      } else if (transcript.status === 'error') {
        throw new Error(`Transcription failed: ${transcript.error}`);
      }

      this.logger.log(`Transcription status: ${transcript.status}`);
      // Wait 5 seconds before polling again
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  }
}
