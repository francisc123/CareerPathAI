import { Controller, All, Res } from '@nestjs/common';

@Controller()
export class ProxyController {
    // Rutarea pentru api/cv/* a fost mutată nativ în main.ts pentru performanță binară stream-to-stream

    @All('ws/hr-interview/:sessionId')
    proxyWsHr(@Res() res: any) {
        res.status(502).send({ message: 'HR Interview WebSocket proxy not yet implemented (CP-027)' });
    }

    @All('ws/tech-interview/:sessionId')
    proxyWsTech(@Res() res: any) {
        res.status(502).send({ message: 'Tech Interview WebSocket proxy not yet implemented (CP-027)' });
    }
}