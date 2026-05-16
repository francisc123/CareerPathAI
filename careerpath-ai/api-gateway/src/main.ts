import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { FastifyAdapter, NestFastifyApplication } from '@nestjs/platform-fastify';
import fastifyWebsocket from '@fastify/websocket';
import { setupWebSocketRoutes } from './websocket-proxy';

async function bootstrap() {
  // 1. Schimbăm motorul pe Fastify
  const app = await NestFactory.create<NestFastifyApplication>(
      AppModule,
      new FastifyAdapter()
  );

  // 2. Păstrăm setările CORS originale
  app.enableCors({ origin: 'http://localhost:3000', credentials: true });

  // 3. Extragem instanța de Fastify și adăugăm plugin-ul de WebSockets
  const fastifyInstance = app.getHttpAdapter().getInstance();

  await fastifyInstance.register(fastifyWebsocket, {
    options: { maxPayload: 1048576 }
  });

  // 4. Conectăm logica de proxy
  setupWebSocketRoutes(fastifyInstance);

  // 5. Pornim pe portul 8000
  const port = process.env.API_GATEWAY_PORT ?? 8000;
  await app.listen(port, '0.0.0.0');
  console.log(`API Gateway is running on: ${await app.getUrl()}`);
}
bootstrap();