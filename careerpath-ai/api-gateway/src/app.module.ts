import { Module } from '@nestjs/common';
import { APP_GUARD } from '@nestjs/core';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { UsersController } from './user.controller';
import { AuthController } from './auth.controller';
import { ProxyController } from './proxy.controller';
import { JwtAuthGuard } from './jwt-auth.guard'; // Asigură-te că ruta către guard-ul tău e corectă

@Module({
  imports: [],
  controllers: [
    AppController,
    AuthController,
    UsersController,
    ProxyController // Am adăugat controller-ul de proxy
  ],
  providers: [
    AppService,
    {
      provide: APP_GUARD,
      useClass: JwtAuthGuard, // Activează verificarea JWT pe TOATE rutele
    },
  ],
})
export class AppModule {}