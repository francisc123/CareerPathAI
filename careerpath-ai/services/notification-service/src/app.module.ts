import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { EmailService } from './email/email.service';
import { SseController } from './sse/sse.controller';
import { KafkaConsumerService } from './kafka-consumer/kafka-consumer.service';

@Module({
  imports: [HttpModule],
  controllers: [SseController], // SseController este controller-ul HTTP real
  providers: [EmailService, KafkaConsumerService], // KafkaConsumerService consumă în fundal
})
export class AppModule {}