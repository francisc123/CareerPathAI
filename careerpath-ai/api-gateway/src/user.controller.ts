import { Controller, All, Req, Res, UseGuards } from '@nestjs/common';
import { Request, Response } from 'express';
import { JwtAuthGuard } from './jwt-auth.guard';
import axios from 'axios';

@Controller('api/users')
@UseGuards(JwtAuthGuard)
export class UsersController {
    // În interiorul Docker, serviciul Java este accesibil la acest URL
    private readonly userServiceUrl = 'http://host.docker.internal:8001';

    @All('*')
    async proxy(@Req() req: Request, @Res() res: Response) {
        const path = req.url.replace('/api/users', '');
        try {
            const response = await axios({
                method: req.method,
                url: `${this.userServiceUrl}/api/users${path}`,
                data: req.body,
                headers: {
                    ...req.headers,
                    // Eliminăm header-ul host original pentru a nu deruta microserviciul
                    host: 'cp-user-service:8001'
                },
            });
            res.status(response.status).json(response.data);
        } catch (error) {
            if (error.response) {
                res.status(error.response.status).json(error.response.data);
            } else {
                res.status(500).json({ message: 'Gateway error: User-Service is unreachable' });
            }
        }
    }
}