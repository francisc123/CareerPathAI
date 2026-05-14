import { Controller, All, Req, Res, Next } from '@nestjs/common';
import type { Request, Response, NextFunction } from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';


@Controller()
export class ProxyController {
    private readonly cvProxy = createProxyMiddleware({
        target: process.env.CV_SERVICE_URL || 'http://localhost:8002', // Numele containerului Docker
        changeOrigin: true,
        pathRewrite: {
            '^/api/cv': '',
        },
        on: {
            proxyReq: (proxyReq, req: any) => {
                if (req.user) {
                    const userId = req.user.sub || req.user.id;
                    if (userId) {
                        proxyReq.setHeader('x-user-id', userId);
                    }
                }
            }
        }
    });

    // Rutele către CV Service
    @All('api/cv/*')
    proxyCv(@Req() req: Request, @Res() res: Response, @Next() next: NextFunction) {
        this.cvProxy(req, res, next);
    }

    // Stub-uri temporare pentru WebSockets (Task CP-027)
    @All('ws/hr-interview/:sessionId')
    proxyWsHr(@Req() req: Request, @Res() res: Response) {
        res.status(502).json({ message: 'HR Interview WebSocket proxy not yet implemented (CP-027)' });
    }

    @All('ws/tech-interview/:sessionId')
    proxyWsTech(@Req() req: Request, @Res() res: Response) {
        res.status(502).json({ message: 'Tech Interview WebSocket proxy not yet implemented (CP-027)' });
    }
}