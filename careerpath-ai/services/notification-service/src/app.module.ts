import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { EmailService } from './email/email.service';
import { SseController } from './sse/sse.controller';
import { KafkaConsumerService } from './kafka-consumer/kafka-consumer.service';

@Module({
  imports: [HttpModule],
  controllers: [SseController], // SseController este controller-ul HTTP real
  // SseController is exposed as a provider too so KafkaConsumerService can
  // inject it and call pushNotification(). Same singleton instance handles
  // both the HTTP /sse/:userId route and incoming Kafka-driven pushes.
  providers: [EmailService, KafkaConsumerService, SseController],
})
export class AppModule {}