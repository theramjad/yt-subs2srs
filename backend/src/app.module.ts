import { Module } from '@nestjs/common';
import { ProcessingModule } from './modules/processing/processing.module';

@Module({
  imports: [ProcessingModule],
  controllers: [],
  providers: [],
})
export class AppModule {}
