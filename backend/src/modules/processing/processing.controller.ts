import {
  Controller,
  Post,
  Get,
  Body,
  Param,
  Res,
  HttpException,
  HttpStatus,
  Query,
} from '@nestjs/common';
import { Response } from 'express';
import { ProcessingService } from './processing.service';
import * as fs from 'fs';

class ProcessRequestDto {
  youtubeUrl: string;
  assemblyAiApiKey: string;
}

@Controller('api')
export class ProcessingController {
  constructor(private readonly processingService: ProcessingService) {}

  /**
   * POST /api/process
   * Start processing a YouTube video
   */
  @Post('process')
  async startProcessing(@Body() body: ProcessRequestDto) {
    const { youtubeUrl, assemblyAiApiKey } = body;

    if (!youtubeUrl || !assemblyAiApiKey) {
      throw new HttpException(
        'Missing youtubeUrl or assemblyAiApiKey',
        HttpStatus.BAD_REQUEST,
      );
    }

    try {
      const result = await this.processingService.startProcessing(
        youtubeUrl,
        assemblyAiApiKey,
      );
      return result;
    } catch (error) {
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  /**
   * GET /api/status/:jobId
   * Get processing status
   */
  @Get('status/:jobId')
  async getStatus(@Param('jobId') jobId: string) {
    const status = this.processingService.getJobStatus(jobId);

    if (!status) {
      throw new HttpException('Job not found', HttpStatus.NOT_FOUND);
    }

    return status;
  }

  /**
   * GET /api/preview/:jobId
   * Get preview of generated cards
   */
  @Get('preview/:jobId')
  async getPreview(
    @Param('jobId') jobId: string,
    @Query('limit') limit?: string,
  ) {
    try {
      const previewLimit = limit ? parseInt(limit, 10) : 5;
      const preview = await this.processingService.getCardPreview(
        jobId,
        previewLimit,
      );
      return { cards: preview };
    } catch (error) {
      throw new HttpException(error.message, HttpStatus.BAD_REQUEST);
    }
  }

  /**
   * GET /api/download/:jobId
   * Download APKG file and cleanup
   */
  @Get('download/:jobId')
  async downloadApkg(@Param('jobId') jobId: string, @Res() res: Response) {
    const job = this.processingService.getJobStatus(jobId);

    if (!job || job.status !== 'complete' || !job.apkgPath) {
      throw new HttpException(
        'Job not complete or APKG not available',
        HttpStatus.BAD_REQUEST,
      );
    }

    try {
      // Check if file exists
      if (!fs.existsSync(job.apkgPath)) {
        throw new HttpException('APKG file not found', HttpStatus.NOT_FOUND);
      }

      // Send file
      const filename = `${job.videoTitle || 'deck'}.apkg`;
      res.download(job.apkgPath, filename, async (err) => {
        if (err) {
          console.error('Download error:', err);
        } else {
          // Cleanup after successful download
          await this.processingService.cleanupJob(jobId);
        }
      });
    } catch (error) {
      throw new HttpException(
        error.message,
        HttpStatus.INTERNAL_SERVER_ERROR,
      );
    }
  }

  /**
   * GET /api/health
   * Health check endpoint
   */
  @Get('health')
  getHealth() {
    return {
      status: 'ok',
      timestamp: new Date().toISOString(),
    };
  }
}
