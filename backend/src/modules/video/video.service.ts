import { Injectable, Logger } from '@nestjs/common';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as fs from 'fs/promises';
import * as path from 'path';

const execAsync = promisify(exec);

interface ProxyConfig {
  enabled: boolean;
  url: string;
  type: string;
  rotation: boolean;
}

@Injectable()
export class VideoService {
  private readonly logger = new Logger(VideoService.name);

  /**
   * Downloads a YouTube video at 360p resolution using yt-dlp
   * @param youtubeUrl - The YouTube video URL
   * @param outputDir - Directory to save the video
   * @returns Path to the downloaded video file and video title
   */
  async downloadVideo(
    youtubeUrl: string,
    outputDir: string,
  ): Promise<{ videoPath: string; title: string }> {
    this.logger.log(`Starting video download for: ${youtubeUrl}`);

    // Ensure output directory exists
    await fs.mkdir(outputDir, { recursive: true });

    const videoPath = path.join(outputDir, 'video.mp4');

    // Load proxy configuration
    const proxyConfig = await this.loadProxyConfig();
    const proxyArg = proxyConfig.enabled ? `--proxy "${proxyConfig.url}"` : '';

    // Build yt-dlp command
    // Format: best video with height <= 360p
    const command = `yt-dlp ${proxyArg} --format "best[height<=360]" -o "${videoPath}" "${youtubeUrl}"`;

    try {
      this.logger.log('Executing yt-dlp command...');
      const { stdout, stderr } = await execAsync(command, {
        maxBuffer: 1024 * 1024 * 10, // 10MB buffer
      });

      if (stderr) {
        this.logger.warn(`yt-dlp stderr: ${stderr}`);
      }

      // Get video title using yt-dlp
      const titleCommand = `yt-dlp --get-title "${youtubeUrl}"`;
      const { stdout: titleOutput } = await execAsync(titleCommand);
      const title = titleOutput.trim();

      this.logger.log(`Video downloaded successfully: ${title}`);
      return { videoPath, title };
    } catch (error) {
      this.logger.error(`Failed to download video: ${error.message}`);
      throw new Error(`Video download failed: ${error.message}`);
    }
  }

  /**
   * Loads proxy configuration from proxy.config.json
   */
  private async loadProxyConfig(): Promise<ProxyConfig> {
    try {
      const configPath = path.join(__dirname, '../../../proxy.config.json');
      const configData = await fs.readFile(configPath, 'utf-8');
      return JSON.parse(configData);
    } catch (error) {
      this.logger.warn('Failed to load proxy config, using default');
      return {
        enabled: false,
        url: '',
        type: 'residential',
        rotation: true,
      };
    }
  }

  /**
   * Checks if yt-dlp is installed
   */
  async checkYtDlpInstalled(): Promise<boolean> {
    try {
      await execAsync('yt-dlp --version');
      return true;
    } catch (error) {
      return false;
    }
  }
}
