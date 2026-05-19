import { Injectable } from '@nestjs/common';
import { Subject } from 'rxjs';

export interface NotificationEvent {
    userId: string;
    type: string;
    data: any;
}

@Injectable()
export class NotificationBusService {
    private readonly subject = new Subject<NotificationEvent>();

    publish(event: NotificationEvent): void {
        this.subject.next(event);
    }

    asObservable() {
        return this.subject.asObservable();
    }
}
