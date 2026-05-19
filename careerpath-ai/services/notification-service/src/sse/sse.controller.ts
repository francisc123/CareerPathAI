import { Controller, Param, Sse } from '@nestjs/common';
import { Observable } from 'rxjs';
import { filter, map } from 'rxjs/operators';
import { NotificationBusService } from './notification-bus.service';

@Controller('sse')
export class SseController {
    constructor(private readonly bus: NotificationBusService) {}

    // Frontend-ul va face GET pe /sse/{userId}
    @Sse(':userId')
    sse(@Param('userId') userId: string): Observable<MessageEvent> {
        console.log(`[SSE] Client conectat pentru user-ul: ${userId}`);

        return this.bus.asObservable().pipe(
            filter((event) => event.userId === userId),
            map((event) => ({
                data: {
                    type: event.type,
                    ...event.data,
                },
            } as MessageEvent)),
        );
    }
}
