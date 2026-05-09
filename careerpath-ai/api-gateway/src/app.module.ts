import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { UsersController } from './user.controller';
import { AuthController } from './auth.controller';

@Module({
  imports: [],
  controllers: [AppController, AuthController, UsersController],
  providers: [AppService],
})
export class AppModule {}
