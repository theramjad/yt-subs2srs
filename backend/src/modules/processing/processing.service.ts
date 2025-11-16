import { Injectable, Logger } from '@nestjs/common';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';
import { VideoService } from '../video/video.service';
import { AudioService } from '../audio/audio.service';
import { AssemblyAIService } from '../transcription/assemblyai.service';
import { SegmentationService } from '../cards/segmentation.service';
import { AnkiService, AnkiCard } from '../cards/anki.service';

export type JobStatus =
  | 'downloading'
  | 'extracting'
  | 'transcribing'
  | 'segmenting'
  | 'generating'
  | 'creating_deck'
  | 'complete'
  | 'error';

export interface JobState {
  jobId: string;
  status: JobStatus;
  progress: number; // 0-100
  currentStep: string;
  error?: string;
  videoTitle?: string;
  cardsCount?: number;
  apkgPath?: string;
  workDir?: string;
}

@Injectable()
export class ProcessingService {
  private readonly logger = new Logger(ProcessingService.name);
  private jobs: Map<string, JobState> = new Map();

  constructor(
    private readonly videoService: VideoService,
    private readonly audioService: AudioService,
    private readonly assemblyAIService: AssemblyAIService,
    private readonly segmentationService: SegmentationService,
    private readonly ankiService: AnkiService,
  ) {}

  /**
   * Starts processing a YouTube video
   */
  async startProcessing(
    youtubeUrl: string,
    assemblyAiApiKey: string,
  ): Promise<{ jobId: string; status: JobStatus }> {
    const jobId = uuidv4();
    const workDir = path.join(os.tmpdir(), 'subs2srs', jobId);

    // Initialize job state
    this.jobs.set(jobId, {
      jobId,
      status: 'downloading',
      progress: 0,
      currentStep: 'Initializing...',
      workDir,
    });

    this.logger.log(`Started job ${jobId} for URL: ${youtubeUrl}`);

    // Start processing asynchronously
    this.processVideo(jobId, youtubeUrl, assemblyAiApiKey, workDir).catch(
      (error) => {
        this.logger.error(`Job ${jobId} failed: ${error.message}`);
        this.updateJobState(jobId, {
          status: 'error',
          error: error.message,
        });
      },
    );

    return { jobId, status: 'downloading' };
  }

  /**
   * Main processing pipeline
   */
  private async processVideo(
    jobId: string,
    youtubeUrl: string,
    assemblyAiApiKey: string,
    workDir: string,
  ): Promise<void> {
    try {
      // Step 1: Download video
      this.updateJobState(jobId, {
        status: 'downloading',
        progress: 5,
        currentStep: 'Downloading video at 360p...',
      });

      const { videoPath, title } = await this.videoService.downloadVideo(
        youtubeUrl,
        workDir,
      );

      this.updateJobState(jobId, {
        videoTitle: title,
        progress: 15,
      });

      // Step 2: Extract audio
      this.updateJobState(jobId, {
        status: 'extracting',
        progress: 20,
        currentStep: 'Extracting audio...',
      });

      const audioPath = await this.audioService.extractAudio(
        videoPath,
        workDir,
      );

      // Step 3: Transcribe with AssemblyAI
      this.updateJobState(jobId, {
        status: 'transcribing',
        progress: 30,
        currentStep: 'Transcribing audio (this may take several minutes)...',
      });

      const words = await this.assemblyAIService.transcribeAudio(
        audioPath,
        assemblyAiApiKey,
      );

      // Step 4: Segment into sentences
      this.updateJobState(jobId, {
        status: 'segmenting',
        progress: 60,
        currentStep: 'Segmenting into sentences...',
      });

      const sentences = this.segmentationService.segmentIntoSentences(words);
      const validSentences =
        this.segmentationService.filterValidSentences(sentences);

      this.logger.log(
        `Job ${jobId}: Created ${validSentences.length} valid sentences`,
      );

      // Re-download video for screenshots (we deleted it earlier)
      this.updateJobState(jobId, {
        progress: 65,
        currentStep: 'Re-downloading video for screenshots...',
      });

      const { videoPath: videoPath2 } = await this.videoService.downloadVideo(
        youtubeUrl,
        workDir,
      );

      // Step 5: Generate cards (audio clips + screenshots)
      this.updateJobState(jobId, {
        status: 'generating',
        progress: 70,
        currentStep: `Generating ${validSentences.length} cards...`,
      });

      const cards = await this.ankiService.generateCards(
        validSentences,
        videoPath2,
        audioPath,
        workDir,
      );

      // Delete video again to save space
      await fs.unlink(videoPath2);

      // Step 6: Create APKG
      this.updateJobState(jobId, {
        status: 'creating_deck',
        progress: 90,
        currentStep: 'Creating Anki deck package...',
      });

      const apkgPath = path.join(workDir, `${title}.apkg`);
      await this.ankiService.createApkg(cards, title, workDir, apkgPath);

      // Complete
      this.updateJobState(jobId, {
        status: 'complete',
        progress: 100,
        currentStep: 'Complete!',
        cardsCount: cards.length,
        apkgPath,
      });

      this.logger.log(`Job ${jobId} completed successfully`);
    } catch (error) {
      throw error;
    }
  }

  /**
   * Gets current job status
   */
  getJobStatus(jobId: string): JobState | undefined {
    return this.jobs.get(jobId);
  }

  /**
   * Gets preview of generated cards
   */
  async getCardPreview(jobId: string, limit: number = 5): Promise<any[]> {
    const job = this.jobs.get(jobId);
    if (!job || job.status !== 'complete') {
      throw new Error('Job not complete or not found');
    }

    // Read cards data from the generated JSON file
    const cardsDataPath = path.join(job.workDir!, 'cards_data.json');
    const data = JSON.parse(await fs.readFile(cardsDataPath, 'utf-8'));

    const previewCards = data.cards.slice(0, limit);

    // Convert media files to base64 for preview
    const preview = await Promise.all(
      previewCards.map(async (card: AnkiCard) => {
        const imageBase64 = await fs.readFile(card.imageFile, 'base64');
        const audioBase64 = await fs.readFile(card.audioFile, 'base64');

        return {
          sentence: card.sentence,
          image: `data:image/webp;base64,${imageBase64}`,
          audio: `data:audio/mp3;base64,${audioBase64}`,
        };
      }),
    );

    return preview;
  }

  /**
   * Cleans up job files after download
   */
  async cleanupJob(jobId: string): Promise<void> {
    const job = this.jobs.get(jobId);
    if (!job || !job.workDir) {
      return;
    }

    this.logger.log(`Cleaning up job ${jobId}`);

    try {
      await fs.rm(job.workDir, { recursive: true, force: true });
      this.jobs.delete(jobId);
      this.logger.log(`Job ${jobId} cleaned up`);
    } catch (error) {
      this.logger.error(`Failed to cleanup job ${jobId}: ${error.message}`);
    }
  }

  /**
   * Updates job state
   */
  private updateJobState(jobId: string, updates: Partial<JobState>): void {
    const current = this.jobs.get(jobId);
    if (current) {
      this.jobs.set(jobId, { ...current, ...updates });
    }
  }
}
