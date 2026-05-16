import { Injectable, Logger, OnModuleInit } from '@nestjs/common';
import * as nodemailer from 'nodemailer';
import * as webpush from 'web-push';
import * as fs from 'fs/promises';
import * as path from 'path';
import { Redis } from 'ioredis';

@Injectable()
export class EmailService implements OnModuleInit {
    private readonly logger = new Logger(EmailService.name);
    private transporter: nodemailer.Transporter;
    private redis: Redis;

    onModuleInit() {
        // Inițializare Nodemailer pentru MailHog
        this.transporter = nodemailer.createTransport({
            host: process.env.SMTP_HOST || 'localhost',
            port: parseInt(process.env.SMTP_PORT || '1025', 10),
            auth: {
                user: process.env.SMTP_USER || '',
                pass: process.env.SMTP_PASS || '',
            },
        });

        // Inițializare Web Push chei VAPID
        webpush.setVapidDetails(
            'mailto:admin@careerpathai.com',
            process.env.VAPID_PUBLIC_KEY || 'default_public_key',
            process.env.VAPID_PRIVATE_KEY || 'default_private_key'
        );

        // Inițializare Redis client pentru subscripții push
        this.redis = new Redis({
            host: process.env.SPRING_DATA_REDIS_HOST || 'localhost',
            port: 6379,
        });
    }

    async sendHtmlEmail(to: string, subject: string, templateName: string, variables: Record<string, any>, customContent?: string): Promise<void> {
        try {
            // Reperul folderului dist/src/templates sau src/templates
            const templatePath = path.join(process.cwd(), 'src', 'templates', `${templateName}.html`);
            let html = await fs.readFile(templatePath, 'utf-8');

            if (customContent) {
                html = html.replace(`{{${templateName}_placeholder}}`, customContent);
            }

            for (const [key, value] of Object.entries(variables)) {
                html = html.replace(new RegExp(`{{${key}}}`, 'g'), String(value));
            }

            await this.transporter.sendMail({
                from: process.env.EMAIL_FROM || '"CareerPathAI" <no-reply@careerpathai.com>',
                to,
                subject,
                html,
            });
            this.logger.log(`Email trimis cu succes către: ${to} (Template: ${templateName})`);
        } catch (error) {
            this.logger.error(`Eroare la trimiterea email-ului către ${to}: ${error.message}`);
        }
    }

    async sendPushNotification(userId: string, title: string, body: string): Promise<void> {
        try {
            const subscriptionData = await this.redis.get(`push:sub:${userId}`);
            if (!subscriptionData) {
                this.logger.log(`Nu există subscripție Web Push în Redis pentru user-ul: ${userId}`);
                return;
            }

            const subscription = JSON.parse(subscriptionData);
            const payload = JSON.stringify({ notification: { title, body } });

            await webpush.sendNotification(subscription, payload);
            this.logger.log(`Web Push trimis cu succes către user-ul: ${userId}`);
        } catch (error) {
            this.logger.error(`Eroare la trimiterea Web Push pentru user ${userId}: ${error.message}`);
        }
    }
}