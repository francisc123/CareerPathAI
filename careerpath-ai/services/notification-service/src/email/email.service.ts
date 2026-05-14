import { Injectable, Logger } from '@nestjs/common';

@Injectable()
export class EmailService {
    private readonly logger = new Logger(EmailService.name);

    async sendEmail(email: string, subject: string, templateData: any): Promise<void> {
        this.logger.log(`[STUB] Trimit email către: ${email}`);
        this.logger.log(`[STUB] Subiect: ${subject}`);
        this.logger.log(`[STUB] Date: ${JSON.stringify(templateData)}`);
    }
}