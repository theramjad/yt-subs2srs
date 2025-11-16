import { Injectable, Logger } from '@nestjs/common';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as path from 'path';

const execAsync = promisify(exec);

@Injectable()
export class ScreenshotService {
  private readonly logger = new Logger(ScreenshotService.name);

  /**
   * Extracts a screenshot from video at a specific timestamp
   * @param videoPath - Path to the video file
   * @param timestamp - Time in seconds
   * @param outputPath - Path for the output screenshot
   * @param resolution - Resolution string (default: 640x360)
   */
  async extractScreenshot(
    videoPath: string,
    timestamp: number,
    outputPath: string,
    resolution: string = '640x360',
  ): Promise<void> {
    this.logger.log(`Extracting screenshot at ${timestamp}s`);

    // FFmpeg command:
    // -ss: seek to timestamp (before -i for faster seeking)
    // -i: input file
    // -frames:v 1: extract single frame
    // -q:v 2: quality (2 is high quality)
    // -s: scale to resolution
    const command = `ffmpeg -ss ${timestamp} -i "${videoPath}" -frames:v 1 -q:v 2 -s ${resolution} "${outputPath}"`;

    try {
      await execAsync(command);
      this.logger.log(`Screenshot saved: ${outputPath}`);
    } catch (error) {
      this.logger.error(`Failed to extract screenshot: ${error.message}`);
      throw new Error(`Screenshot extraction failed: ${error.message}`);
    }
  }

  /**
   * Extracts multiple screenshots for a batch of timestamps
   * @param videoPath - Path to the video file
   * @param timestamps - Array of timestamps with their indices
   * @param outputDir - Directory to save screenshots
   * @returns Array of screenshot file paths
   */
  async extractBatchScreenshots(
    videoPath: string,
    timestamps: Array<{ index: number; time: number }>,
    outputDir: string,
  ): Promise<string[]> {
    this.logger.log(`Extracting ${timestamps.length} screenshots...`);

    const screenshotPaths: string[] = [];

    for (const { index, time } of timestamps) {
      const outputPath = path.join(outputDir, `screenshot_${index}.webp`);
      await this.extractScreenshot(videoPath, time, outputPath);
      screenshotPaths.push(outputPath);
    }

    this.logger.log('All screenshots extracted successfully');
    return screenshotPaths;
  }
}
