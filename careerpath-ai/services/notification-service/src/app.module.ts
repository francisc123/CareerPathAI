import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { AppController } from './app.controller';
import { AppService } from './app.service';

import { SseController } from './sse/sse.controller';
import { EmailService } from './email/email.service';
import { KafkaConsumerService } from './kafka-consumer/kafka-consumer.service';

@Module({
  imports: [
    HttpModule,
  ],
  controllers: [AppController, SseController],
  providers: [AppService, EmailService, KafkaConsumerService, SseController],
})
export class AppModule {}