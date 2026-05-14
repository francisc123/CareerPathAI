import { Injectable, OnModuleInit, OnModuleDestroy, Logger } from '@nestjs/common';
import { Kafka, Consumer } from 'kafkajs';
import { HttpService } from '@nestjs/axios';
import { firstValueFrom } from 'rxjs';
import { EmailService } from '../email/email.service';
import { SseController } from '../sse/sse.controller';

@Injectable()
export class KafkaConsumerService implements OnModuleInit, OnModuleDestroy {
    private readonly logger = new Logger(KafkaConsumerService.name);
    private consumer: Consumer;

    constructor(
        private readonly httpService: HttpService,
        private readonly emailService: EmailService,
        private readonly sseController: SseController,
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
                eachMessage: async ({ topic, partition, message }) => {
                    if (!message.value) return;

                    const payload = JSON.parse(message.value.toString());
                    const userId = payload.userId;

                    this.logger.log(`Primit eveniment [${topic}] pentru user [${userId}]`);

                    if (!userId) {
                        this.logger.warn(`Mesajul de pe ${topic} nu are userId! Ignorăm.`);
                        return;
                    }

                    let userEmail = 'unknown@example.com';
                    try {
                        const targetUrl = process.env.USER_SERVICE_URL || 'http://localhost:8001';
                        const response = await firstValueFrom(
                            this.httpService.get(`${targetUrl}/profile/${userId}`)
                        );
                        userEmail = response.data.email;
                    } catch (error) {
                        this.logger.error(`Eroare la fetch profil user ${userId}: ${error.message}`);
                    }

                    await this.emailService.sendEmail(
                        userEmail,
                        `Nou update pentru contul tău: ${topic}`,
                        payload
                    );

                    this.sseController.pushNotification({
                        userId,
                        type: topic,
                        data: payload
                    });
                },
            });
        } catch (error) {
            this.logger.error(`Eroare la inițializarea consumatorului Kafka: ${error.message}`);
        }
    }

    async onModuleDestroy() {
        await this.consumer.disconnect();
        this.logger.log('Deconectat de la Redpanda.');
    }
}