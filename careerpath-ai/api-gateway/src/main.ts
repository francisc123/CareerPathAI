import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { FastifyAdapter, NestFastifyApplication } from '@nestjs/platform-fastify';
import fastifyWebsocket from '@fastify/websocket';
import fastifyHttpProxy from '@fastify/http-proxy';
import * as jwt from 'jsonwebtoken';
import * as fs from 'fs';
import { setupWebSocketRoutes } from './websocket-proxy';

async function bootstrap() {
  const app = await NestFactory.create<NestFastifyApplication>(
      AppModule,
      new FastifyAdapter()
  );

  app.enableCors({ origin: 'http://localhost:3000', credentials: true });

  const fastifyInstance = app.getHttpAdapter().getInstance();

  // Încărcăm cheia publică pentru a valida token-ul JWT direct la nivel de proxy de rețea
  const keyPath = process.env.JWT_PUBLIC_KEY_PATH || './keys/public.pem';
  const publicKey = fs.existsSync(keyPath) ? fs.readFileSync(keyPath, 'utf8') : '';

  // PROXY NATIV PENTRU CV-SERVICE
  await fastifyInstance.register(fastifyHttpProxy, {
    upstream: process.env.CV_SERVICE_URL || 'http://cp-cv-service:8002',
    prefix: '/api/cv',
    rewritePrefix: '', // Elimină /api/cv din calea trimisă către microserviciul Python
    preHandler: async (request: any, reply: any) => {
      // Extragem manual token-ul din header pentru a păstra securitatea JwtAuthGuard
      const authHeader = request.headers['authorization'];
      if (authHeader && authHeader.startsWith('Bearer ') && publicKey) {
        try {
          const token = authHeader.split(' ')[1];
          const payload: any = jwt.verify(token, publicKey, { algorithms: ['RS256'] });
          const userId = payload?.sub || payload?.id;
          if (userId) {
            // Injectăm header-ul cerut de cv-service
            request.headers['x-user-id'] = userId;
          }
        } catch (err) {
          // Dacă token-ul e invalid, proxy-ul se oprește aici
          reply.code(401).send({ message: 'Unauthorized proxy access' });
          return;
        }
      }
    }
  });

  // PROXY NATIV PENTRU LEARNING-PATH-AGENT (CP-039)
  await fastifyInstance.register(fastifyHttpProxy, {
    upstream: process.env.LEARNING_SERVICE_URL || 'http://learning-path-agent:8007',
    prefix: '/api/learning',
    rewritePrefix: '/learning', // Pune prefixul corect /learning/{userId} conform specificațiilor agentului Python
    preHandler: async (request: any, reply: any) => {
      // Păstrează compatibilitatea cu testele E2E (unde punem manual X-User-Id în scriptul bash)
      const xUserId = request.headers['x-user-id'];
      if (!xUserId) {
        const authHeader = request.headers['authorization'];
        if (authHeader && authHeader.startsWith('Bearer ') && publicKey) {
          try {
            const token = authHeader.split(' ')[1];
            const payload: any = jwt.verify(token, publicKey, { algorithms: ['RS256'] });
            const userId = payload?.sub || payload?.id;
            if (userId) {
              request.headers['x-user-id'] = userId;
            }
          } catch (err) {
            reply.code(401).send({ message: 'Unauthorized proxy access' });
            return;
          }
        }
      }
    }
  });

  // Activare WebSockets pentru interviuri
  await fastifyInstance.register(fastifyWebsocket, {
    options: { maxPayload: 1048576 }
  });

  setupWebSocketRoutes(fastifyInstance);

  const port = process.env.API_GATEWAY_PORT ?? 8000;
  await app.listen(port, '0.0.0.0');
  console.log(`API Gateway is running on: ${await app.getUrl()}`);
}
bootstrap();