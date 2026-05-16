import { WebSocket } from 'ws';
import { FastifyInstance, FastifyRequest } from 'fastify';

export function setupWebSocketRoutes(fastifyInstance: FastifyInstance) {

    fastifyInstance.addHook('onRequest', async (request: any, reply: any) => {
        if (request.raw.headers.upgrade && request.raw.headers.upgrade.toLowerCase() === 'websocket') {

            const url = request.raw.url;

            // 1. Match pentru HR Interview
            if (url.startsWith('/ws/hr-interview/')) {
                const pathPart = url.split('?')[0];
                const sessionId = pathPart.split('/').pop();
                const targetUrl = `ws://127.0.0.1:8009/ws/hr/${sessionId}`;

                // Predăm conexiunea către WebSocket
                return handleProxy(request, targetUrl);
            }

            // 2. Match pentru Tech Interview
            if (url.startsWith('/ws/tech-interview/')) {
                const pathPart = url.split('?')[0];
                const sessionId = pathPart.split('/').pop();
                const targetUrl = `ws://127.0.0.1:8010/ws/tech/${sessionId}`;

                return handleProxy(request, targetUrl);
            }
        }
    });

    // Funcția care face tunelul efectiv
    function handleProxy(request: any, targetUrl: string) {
        // Accesăm socket-ul brut expus de @fastify/websocket
        const socket = request.server.websocketServer;

        socket.handleUpgrade(request.raw, request.raw.socket, Buffer.alloc(0), (connection) => {

            // Verificare Token
            const token = request.query?.token;
            if (!token) {
                console.warn('WebSocket connection attempt without token');
                connection.close(1008, 'Token missing');
                return;
            }

            console.log(`Proxying WS to: ${targetUrl}`);
            const upstreamSocket = new WebSocket(targetUrl);

            // Client -> Agent
            connection.on('message', (message: any) => {
                if (upstreamSocket.readyState === WebSocket.OPEN) {
                    upstreamSocket.send(message);
                }
            });

            // Agent -> Client
            upstreamSocket.on('message', (message: any) => {
                if (connection.readyState === WebSocket.OPEN) {
                    connection.send(message);
                }
            });

            // Error handling & Cleanup
            upstreamSocket.on('close', (code: number, reason: any) => {
                connection.close(code, reason.toString());
            });

            connection.on('close', (code: number, reason: any) => {
                upstreamSocket.close(code, reason.toString());
            });

            upstreamSocket.on('error', () => {
                connection.close(1011, 'Upstream error');
            });
        });
    }
}