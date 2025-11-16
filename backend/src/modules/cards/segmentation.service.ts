import { Injectable, Logger } from '@nestjs/common';
import { TranscriptWord } from '../transcription/assemblyai.service';

export interface Sentence {
  text: string;
  startTime: number; // in seconds
  endTime: number; // in seconds
  speaker?: string;
  words: TranscriptWord[];
}

@Injectable()
export class SegmentationService {
  private readonly logger = new Logger(SegmentationService.name);
  private readonly MAX_SENTENCE_LENGTH = 20; // words
  private readonly MIN_SENTENCE_LENGTH = 3; // words

  /**
   * Segments transcript words into sentences based on:
   * - Speaker changes
   * - Punctuation marks (。！？)
   * - Sentence length limits
   */
  segmentIntoSentences(words: TranscriptWord[]): Sentence[] {
    this.logger.log(`Segmenting ${words.length} words into sentences...`);

    const sentences: Sentence[] = [];
    let currentSentence: TranscriptWord[] = [];
    let currentSpeaker = words[0]?.speaker;

    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      const nextWord = words[i + 1];

      currentSentence.push(word);

      // Check if we should split here
      const shouldSplit = this.shouldSplitSentence(
        word,
        nextWord,
        currentSentence.length,
        currentSpeaker,
      );

      if (shouldSplit || i === words.length - 1) {
        // Create sentence if it meets minimum length
        if (currentSentence.length >= this.MIN_SENTENCE_LENGTH) {
          sentences.push(this.createSentence(currentSentence));
        } else if (i === words.length - 1 && currentSentence.length > 0) {
          // Include short final sentences
          sentences.push(this.createSentence(currentSentence));
        }

        // Reset for next sentence
        currentSentence = [];
        if (nextWord) {
          currentSpeaker = nextWord.speaker;
        }
      }
    }

    this.logger.log(`Created ${sentences.length} sentences`);
    return sentences;
  }

  /**
   * Determines if a sentence should be split at the current position
   */
  private shouldSplitSentence(
    currentWord: TranscriptWord,
    nextWord: TranscriptWord | undefined,
    wordsSinceLastSplit: number,
    currentSpeaker: string | undefined,
  ): boolean {
    if (!nextWord) {
      return true; // End of transcript
    }

    // Speaker change
    if (currentWord.speaker !== nextWord.speaker) {
      return true;
    }

    // Punctuation marks (Japanese sentence endings)
    const hasPunctuation = /[。！？]/.test(currentWord.text);

    // Split on punctuation if sentence is getting long
    if (hasPunctuation && wordsSinceLastSplit >= 8) {
      return true;
    }

    // Force split if sentence is too long
    if (wordsSinceLastSplit >= this.MAX_SENTENCE_LENGTH) {
      // Try to split at a natural pause
      if (hasPunctuation || /[、\s]/.test(currentWord.text)) {
        return true;
      }
    }

    return false;
  }

  /**
   * Creates a Sentence object from a list of words
   */
  private createSentence(words: TranscriptWord[]): Sentence {
    if (words.length === 0) {
      throw new Error('Cannot create sentence from empty word list');
    }

    const text = words.map((w) => w.text).join('');
    const startTime = words[0].start;
    const endTime = words[words.length - 1].end;
    const speaker = words[0].speaker;

    return {
      text,
      startTime,
      endTime,
      speaker,
      words,
    };
  }

  /**
   * Filters out sentences that are too short or likely noise
   */
  filterValidSentences(sentences: Sentence[]): Sentence[] {
    return sentences.filter((sentence) => {
      // Must have at least minimum word count
      if (sentence.words.length < this.MIN_SENTENCE_LENGTH) {
        return false;
      }

      // Must have some Japanese characters
      if (!/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]/.test(sentence.text)) {
        return false;
      }

      return true;
    });
  }
}
