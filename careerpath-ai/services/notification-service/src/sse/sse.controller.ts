import { Controller, Get, Param, Sse } from '@nestjs/common';
import { Observable, Subject } from 'rxjs';
import { filter, map } from 'rxjs/operators';

export interface NotificationEvent {
    userId: string;
    type: string;
    data: any;
}

@Controller('sse')
export class SseController {
    private notificationsSubject = new Subject<NotificationEvent>();

    pushNotification(event: NotificationEvent) {
        this.notificationsSubject.next(event);
    }

    // Frontend-ul va face GET pe /sse/{userId}
    @Sse(':userId')
    sse(@Param('userId') userId: string): Observable<MessageEvent> {
        console.log(`[SSE] Client conectat pentru user-ul: ${userId}`);

        return this.notificationsSubject.asObservable().pipe(
            filter((event) => event.userId === userId),
            map((event) => {
                return {
                    data: {
                        type: event.type,
                        ...event.data,
                    },
                } as MessageEvent;
            }),
        );
    }
}