import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // CORS este esențial pentru ca browser-ul să poată deschide fluxul SSE
  app.enableCors({
    origin: true,
    methods: 'GET, HEAD, PUT, PATCH, POST, DELETE, OPTIONS',
    credentials: true,
  });

  await app.listen(8004);
  console.log(`Notification Service is running on: http://localhost:8004`);
}
bootstrap();