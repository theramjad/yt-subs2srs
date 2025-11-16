import { Injectable, Logger } from '@nestjs/common';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';

const execAsync = promisify(exec);

@Injectable()
export class AudioService {
  private readonly logger = new Logger(AudioService.name);

  /**
   * Extracts audio from video file as MP3 at 128kbps
   * @param videoPath - Path to the input video file
   * @param outputDir - Directory to save the audio file
   * @returns Path to the extracted audio file
   */
  async extractAudio(
    videoPath: string,
    outputDir: string,
  ): Promise<string> {
    this.logger.log(`Extracting audio from: ${videoPath}`);

    const audioPath = path.join(outputDir, 'audio.mp3');

    // FFmpeg command: Extract MP3 at 128kbps, 44.1kHz sample rate, stereo
    const command = `ffmpeg -i "${videoPath}" -vn -ar 44100 -ac 2 -b:a 128k "${audioPath}"`;

    try {
      const { stderr } = await execAsync(command, {
        maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      });

      if (stderr && stderr.includes('error')) {
        this.logger.warn(`FFmpeg warnings: ${stderr}`);
      }

      this.logger.log('Audio extracted successfully');

      // Delete the video file to save space
      await fs.unlink(videoPath);
      this.logger.log('Video file deleted');

      return audioPath;
    } catch (error) {
      this.logger.error(`Failed to extract audio: ${error.message}`);
      throw new Error(`Audio extraction failed: ${error.message}`);
    }
  }

  /**
   * Extracts audio clip from full audio file with padding
   * @param audioPath - Path to the source audio file
   * @param startTime - Start time in seconds
   * @param endTime - End time in seconds
   * @param outputPath - Path for the output clip
   * @param padding - Padding in seconds (default: 0.25)
   */
  async extractAudioClip(
    audioPath: string,
    startTime: number,
    endTime: number,
    outputPath: string,
    padding: number = 0.25,
  ): Promise<void> {
    const paddedStart = Math.max(0, startTime - padding);
    const paddedEnd = endTime + padding;

    // Use -ss before -i for faster seeking, -c copy for stream copy (faster)
    const command = `ffmpeg -ss ${paddedStart} -i "${audioPath}" -to ${paddedEnd - paddedStart} -c copy "${outputPath}"`;

    try {
      await execAsync(command);
      this.logger.log(`Audio clip extracted: ${outputPath}`);
    } catch (error) {
      // If stream copy fails, try re-encoding
      this.logger.warn('Stream copy failed, trying re-encode...');
      const reencodeCommand = `ffmpeg -ss ${paddedStart} -i "${audioPath}" -to ${paddedEnd - paddedStart} -b:a 128k "${outputPath}"`;
      await execAsync(reencodeCommand);
      this.logger.log(`Audio clip extracted with re-encoding: ${outputPath}`);
    }
  }

  /**
   * Checks if FFmpeg is installed
   */
  async checkFfmpegInstalled(): Promise<boolean> {
    try {
      await execAsync('ffmpeg -version');
      return true;
    } catch (error) {
      return false;
    }
  }
}
