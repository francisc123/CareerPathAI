import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { Kafka, Consumer } from 'kafkajs';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { EmailService } from '../email/email.service';
import { NotificationBusService } from '../sse/notification-bus.service';

@Injectable()
export class KafkaConsumerService implements OnModuleInit, OnModuleDestroy {
    private readonly logger = new Logger(KafkaConsumerService.name);
    private consumer: Consumer;

    constructor(
        private readonly httpService: HttpService,
        private readonly emailService: EmailService,
        private readonly bus: NotificationBusService,
    ) {
        const kafka = new Kafka({
            clientId: process.env.KAFKA_CLIENT_ID || 'careerpath-ai-notifications',
            brokers: [process.env.KAFKA_BROKERS || 'localhost:19092'],
        });
        this.consumer = kafka.consumer({ groupId: 'notification-service-group' });
    }

    async onModuleInit() {
        try {
            await this.consumer.connect();
            this.logger.log('Conectat la Redpanda cu succes!');

            const topics = [
                'cv.analyzed',
                'jobs.matched',
                'learning.path.created',
                'interview.hr.completed',
                'interview.tech.completed'
            ];

            for (const topic of topics) {
                await this.consumer.subscribe({ topic, fromBeginning: false });
                this.logger.log(`Subscris la topicul: ${topic}`);
            }

            await this.consumer.run({
                eachMessage: async ({ topic, message }) => {
                    if (!message.value) return;

                    const payload = JSON.parse(message.value.toString());
                    const userId = payload.userId || payload.user_id;

                    if (!userId) {
                        this.logger.warn(`Mesajul de pe topicul ${topic} nu conține userId!`);
                        return;
                    }

                    this.logger.log(`Procesez eveniment [${topic}] pentru utilizatorul [${userId}]`);

                    // 1. Preluare email profil din User Service
                    let userEmail = 'student@unstpb.ro';
                    try {
                        const targetUrl = process.env.USER_SERVICE_URL || 'http://localhost:8001';
                        const response = await firstValueFrom(
                            this.httpService.get(`${targetUrl}/profile/${userId}`)
                        );
                        userEmail = response.data.email;
                    } catch (error) {
                        this.logger.error(`Fetch profil eșuat pentru ${userId}, folosesc fallback email.`);
                    }

                    // 2. Trimitere simultană pe cele 3 canale (SSE + Web Push + Email HTML)
                    this.bus.publish({ userId, type: topic, data: payload });

                    switch (topic) {
                        case 'cv.analyzed':
                            await this.emailService.sendPushNotification(userId, 'CV Analysis Complete', `Your parser score is ${payload.score}%.`);
                            await this.emailService.sendHtmlEmail(userEmail, 'CareerPathAI - CV Analysis Complete', 'cv-analyzed', { score: payload.score || 0 });
                            break;

                        case 'jobs.matched':
                            let jobsHtml = '';
                            const matches = payload.matches || [];
                            matches.slice(0, 3).forEach((j: any) => {
                                jobsHtml += `
                                    <div style="padding: 15px; border-bottom: 1px solid #eee;">
                                        <strong>${j.title} - ${j.company}</strong>
                                        <p>Score: ${j.match_score || j.matchScore}% | Location: ${j.location}</p>
                                        <a href="${j.url}" style="color: #10B981;">View Details</a>
                                    </div>`;
                            });

                            await this.emailService.sendPushNotification(userId, 'New Job Matches!', `We found ${matches.length} job matches.`);
                            await this.emailService.sendHtmlEmail(userEmail, 'CareerPathAI - New Job Matches Found', 'jobs-matched', {}, jobsHtml);
                            break;

                        case 'learning.path.created':
                            await this.emailService.sendPushNotification(userId, 'Curriculum Generated', 'Your custom week-by-week plan is ready.');
                            await this.emailService.sendHtmlEmail(userEmail, 'Your Customized Learning Plan', 'learning-path-created', { summary: payload.summary || '' });
                            break;

                        case 'interview.hr.completed':
                        case 'interview.tech.completed':
                            await this.emailService.sendPushNotification(userId, 'Interview Scores Released', 'Evaluation complete.');
                            await this.emailService.sendHtmlEmail(userEmail, 'AI Simulation Interview Evaluation', 'interview-feedback', {
                                hrScore: payload.hrScore || 0,
                                techScore: payload.techScore || 0,
                                improvementAreas: payload.improvementAreas || 'N/A'
                            });
                            break;
                    }
                },
            });
        } catch (error) {
            this.logger.error(`Eroare critică în consumer-ul Kafka: ${error.message}`);
        }
    }

    async onModuleDestroy() {
        await this.consumer.disconnect();
        this.logger.log('Deconectat de la Redpanda.');
    }
}