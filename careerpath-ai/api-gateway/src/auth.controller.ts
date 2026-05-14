import { Controller, Post, Get, Body, BadRequestException, UseGuards, Req } from '@nestjs/common';
import type { Request } from 'express';
import * as jwt from 'jsonwebtoken';
import * as fs from 'fs';
import { JwtAuthGuard } from './jwt-auth.guard';

import { Public } from './auth/public.decorator';

interface LoginDto { email: string; password: string; }
interface RegisterDto { name: string; email: string; password: string; }

@Controller('api/auth')
export class AuthController {
    private readonly privateKey: string;

    constructor() {
        const keyPath = process.env.JWT_PRIVATE_KEY_PATH || './keys/private.pem';
        this.privateKey = fs.existsSync(keyPath) ? fs.readFileSync(keyPath, 'utf8') : '';
    }

    private sign(payload: object): string {
        if (!this.privateKey) throw new BadRequestException('JWT private key not configured');
        return jwt.sign(payload, this.privateKey, { algorithm: 'RS256', expiresIn: '15m' });
    }

    @Public()
    @Post('login')
    login(@Body() body: LoginDto) {
        if (!body.email || !body.password) throw new BadRequestException('Email și parola sunt obligatorii');
        const userId = Buffer.from(body.email).toString('base64url');
        const user = { id: userId, email: body.email, name: body.email.split('@')[0] };
        return { user, token: this.sign({ sub: userId, email: body.email, name: user.name }) };
    }

    @Public()
    @Post('register')
    register(@Body() body: RegisterDto) {
        if (!body.email || !body.password || !body.name) throw new BadRequestException('Toate câmpurile sunt obligatorii');
        const userId = Buffer.from(body.email).toString('base64url');
        const user = { id: userId, email: body.email, name: body.name };
        return { user, token: this.sign({ sub: userId, email: body.email, name: body.name }) };
    }

    @Get('me')
    getMe(@Req() req: Request) {
        return (req as any).user;
    }
}
