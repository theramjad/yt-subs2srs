import { Injectable, Logger } from '@nestjs/common';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';
import { Sentence } from './segmentation.service';
import { AudioService } from '../audio/audio.service';
import { ScreenshotService } from './screenshot.service';

const execAsync = promisify(exec);

export interface AnkiCard {
  audioFile: string;
  imageFile: string;
  sentence: string;
}

@Injectable()
export class AnkiService {
  private readonly logger = new Logger(AnkiService.name);

  constructor(
    private readonly audioService: AudioService,
    private readonly screenshotService: ScreenshotService,
  ) {}

  /**
   * Generates Anki cards from sentences
   * @param sentences - Segmented sentences
   * @param videoPath - Path to video file (for screenshots)
   * @param audioPath - Path to full audio file
   * @param outputDir - Directory to save card media
   * @returns Array of AnkiCard objects
   */
  async generateCards(
    sentences: Sentence[],
    videoPath: string,
    audioPath: string,
    outputDir: string,
  ): Promise<AnkiCard[]> {
    this.logger.log(`Generating ${sentences.length} Anki cards...`);

    const cards: AnkiCard[] = [];

    for (let i = 0; i < sentences.length; i++) {
      const sentence = sentences[i];
      this.logger.log(`Processing card ${i + 1}/${sentences.length}`);

      // Extract audio clip with 250ms padding
      const audioClipPath = path.join(outputDir, `clip_${i}.mp3`);
      await this.audioService.extractAudioClip(
        audioPath,
        sentence.startTime,
        sentence.endTime,
        audioClipPath,
        0.25, // 250ms padding
      );

      // Extract screenshot at sentence start time
      const screenshotPath = path.join(outputDir, `screenshot_${i}.webp`);
      await this.screenshotService.extractScreenshot(
        videoPath,
        sentence.startTime,
        screenshotPath,
      );

      cards.push({
        audioFile: audioClipPath,
        imageFile: screenshotPath,
        sentence: sentence.text,
      });
    }

    this.logger.log(`Generated ${cards.length} cards successfully`);
    return cards;
  }

  /**
   * Creates APKG file from cards using genanki Python script
   * @param cards - Array of AnkiCard objects
   * @param deckName - Name for the Anki deck
   * @param outputDir - Directory for temporary files
   * @param outputPath - Path for the output APKG file
   */
  async createApkg(
    cards: AnkiCard[],
    deckName: string,
    outputDir: string,
    outputPath: string,
  ): Promise<string> {
    this.logger.log(`Creating APKG file: ${deckName}`);

    // Create cards data JSON file for Python script
    const cardsDataPath = path.join(outputDir, 'cards_data.json');
    const cardsData = {
      deckName,
      cards,
      mediaDir: outputDir,
    };

    await fs.writeFile(
      cardsDataPath,
      JSON.stringify(cardsData, null, 2),
      'utf-8',
    );

    // Get path to Python script
    const scriptPath = path.join(__dirname, '../../scripts/generate_apkg.py');

    // Execute Python script
    const command = `python3 "${scriptPath}" "${cardsDataPath}" "${outputPath}"`;

    try {
      const { stdout, stderr } = await execAsync(command);

      if (stdout) {
        this.logger.log(`Python script output: ${stdout}`);
      }
      if (stderr) {
        this.logger.warn(`Python script warnings: ${stderr}`);
      }

      this.logger.log('APKG file created successfully');
      return outputPath;
    } catch (error) {
      this.logger.error(`Failed to create APKG: ${error.message}`);
      throw new Error(`APKG creation failed: ${error.message}`);
    }
  }

  /**
   * Checks if Python and genanki are installed
   */
  async checkPythonSetup(): Promise<{
    pythonInstalled: boolean;
    genankiInstalled: boolean;
  }> {
    let pythonInstalled = false;
    let genankiInstalled = false;

    try {
      await execAsync('python3 --version');
      pythonInstalled = true;
    } catch (error) {
      this.logger.warn('Python3 not found');
    }

    if (pythonInstalled) {
      try {
        await execAsync('python3 -c "import genanki"');
        genankiInstalled = true;
      } catch (error) {
        this.logger.warn('genanki not installed');
      }
    }

    return { pythonInstalled, genankiInstalled };
  }
}
