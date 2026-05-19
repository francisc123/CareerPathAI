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
        // Demo-friendly 24h expiry. Refresh-token flow isn't wired yet, so a short
        // expiry would log everyone out mid-demo.
        return jwt.sign(payload, this.privateKey, { algorithm: 'RS256', expiresIn: '24h' });
    }

    @Public()
    @Post('login')
    async login(@Body() body: LoginDto) {
        if (!body.email || !body.password) {
            throw new BadRequestException('Email și parola sunt obligatorii');
        }

        try {
            // Trimitem datele de logare către user-service pentru verificare în baza de date
            const upstream = await fetch('http://cp-user-service:8001/api/users/verify-credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    email: body.email,
                    password: body.password
                }),
            });

            const data = await upstream.json().catch(() => ({}));

            if (!upstream.ok) {
                throw new BadRequestException(data.message || 'Credențiale invalide');
            }

            // Dacă Spring Boot a confirmat utilizatorul, extragem datele lui reale salvate în Postgres
            const userId = data.id;
            const user = { id: userId, email: data.email, name: data.username || data.email.split('@')[0] };

            // Generăm token-ul oficial de sesiune bazat pe ID-ul real din baza de date
            return {
                user,
                token: this.sign({ sub: userId, email: user.email, name: user.name })
            };

        } catch (error) {
            if (error instanceof BadRequestException) throw error;
            throw new BadRequestException('Nu s-a putut efectua autentificarea dintr-o eroare internă a gateway-ului');
        }
    }

    @Public()
    @Post('register')
    async register(@Body() body: RegisterDto) {
        if (!body.email || !body.password || !body.name) {
            throw new BadRequestException('Toate câmpurile sunt obligatorii');
        }

        // Generăm ID-ul stabil local pe baza emailului
        const userId = Buffer.from(body.email).toString('base64url');

        try {
            // Trimitem datele către noul endpoint public din user-service
            const upstream = await fetch('http://cp-user-service:8001/api/users/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id: userId,
                    email: body.email,
                    username: body.name
                }),
            });

            const data = await upstream.json().catch(() => ({}));

            if (!upstream.ok) {
                throw new BadRequestException('Eroare la persistarea utilizatorului în baza de date locală');
            }

            const user = { id: userId, email: body.email, name: body.name };
            return {
                user,
                token: this.sign({ sub: userId, email: body.email, name: body.name })
            };

        } catch (error) {
            if (error instanceof BadRequestException) throw error;
            throw new BadRequestException('Microserviciul User-Service nu a putut fi accesat');
        }
    }

    @Get('me')
    getMe(@Req() req: Request) {
        return (req as any).user;
    }
}
