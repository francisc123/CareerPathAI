import { Controller, All, Req, Res, UseGuards } from '@nestjs/common';
import type { Request, Response } from 'express';
import { JwtAuthGuard } from './jwt-auth.guard';

@Controller('api/users')
@UseGuards(JwtAuthGuard)
export class UsersController {
    private readonly userServiceUrl = 'http://cp-user-service:8001';

    @All('*')
    async proxy(@Req() req: Request, @Res() res: Response) {
        const path = req.url.replace('/api/users', '');
        try {
            const upstream = await fetch(`${this.userServiceUrl}/api/users${path}`, {
                method: req.method,
                headers: {
                    'content-type': 'application/json',
                    'x-user-id': req.headers['x-user-id'] as string ?? '',
                },
                body: ['GET', 'HEAD'].includes(req.method) ? undefined : JSON.stringify(req.body),
            });
            const data = await upstream.json().catch(() => ({}));
            res.status(upstream.status).json(data);
        } catch (error) {
            res.status(500).json({ message: 'Gateway error: User-Service is unreachable' });
        }
    }
}
