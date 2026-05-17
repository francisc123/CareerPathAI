import { Controller, All, Req, Res, UseGuards } from '@nestjs/common';
import type { FastifyRequest, FastifyReply } from 'fastify';
import { JwtAuthGuard } from './jwt-auth.guard';

@Controller('api/users')
@UseGuards(JwtAuthGuard)
export class UsersController {
    private readonly userServiceUrl = 'http://cp-user-service:8001';

    @All('*')
    async proxy(@Req() req: FastifyRequest, @Res() res: FastifyReply) {
        const path = req.url.replace('/api/users', '');
        try {
            const upstream = await fetch(`${this.userServiceUrl}/api/users${path}`, {
                method: req.method,
                headers: {
                    'content-type': 'application/json',
                    'x-user-id': (req.headers['x-user-id'] as string) ?? '',
                },
                body: ['GET', 'HEAD'].includes(req.method)
                    ? undefined
                    : JSON.stringify(req.body),
            });
            const data = await upstream.json().catch(() => ({}));
            return res.code(upstream.status).send(data);
        } catch (error) {
            return res.code(502).send({ message: 'Gateway error: User-Service is unreachable' });
        }
    }
}