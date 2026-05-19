import { Module } from '@nestjs/common';
import { HttpModule } from '@nestjs/axios';
import { EmailService } from './email/email.service';
import { SseController } from './sse/sse.controller';
import { NotificationBusService } from './sse/notification-bus.service';
import { KafkaConsumerService } from './kafka-consumer/kafka-consumer.service';

@Module({
  imports: [HttpModule],
  controllers: [SseController],
  providers: [EmailService, KafkaConsumerService, NotificationBusService],
})
export class AppModule {}
