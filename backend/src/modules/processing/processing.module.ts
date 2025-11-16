import { Module } from '@nestjs/common';
import { ProcessingController } from './processing.controller';
import { ProcessingService } from './processing.service';
import { VideoService } from '../video/video.service';
import { AudioService } from '../audio/audio.service';
import { AssemblyAIService } from '../transcription/assemblyai.service';
import { SegmentationService } from '../cards/segmentation.service';
import { ScreenshotService } from '../cards/screenshot.service';
import { AnkiService } from '../cards/anki.service';

@Module({
  controllers: [ProcessingController],
  providers: [
    ProcessingService,
    VideoService,
    AudioService,
    AssemblyAIService,
    SegmentationService,
    ScreenshotService,
    AnkiService,
  ],
})
export class ProcessingModule {}
