import { NestFactory } from '@nestjs/core';
import { Module } from '@nestjs/common';
import { Controller, Get } from '@nestjs/common';

@Controller()
class HealthController {
  @Get('/health')
  health() {
    return { status: 'ok', service: 'notification-service' };
  }
}

@Module({ controllers: [HealthController] })
class AppModule {}

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  await app.listen(8004);
  console.log('Notification Service (stub) running on port 8004');
}
bootstrap();
