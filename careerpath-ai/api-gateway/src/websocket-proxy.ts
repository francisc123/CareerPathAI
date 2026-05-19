import { WebSocket } from 'ws';
import { FastifyInstance } from 'fastify';

export function setupWebSocketRoutes(fastifyInstance: FastifyInstance) {

    fastifyInstance.addHook('onRequest', async (request: any, reply: any) => {
        if (request.raw.headers.upgrade && request.raw.headers.upgrade.toLowerCase() === 'websocket') {

            const url = request.raw.url || '';
            const pathPart = url.split('?')[0];
            const query = url.includes('?') ? url.split('?').slice(1).join('?') : '';

            // 1. Match pentru HR Interview
            if (pathPart.startsWith('/ws/hr-interview/')) {
                const sessionId = pathPart.split('/').pop();
                // Upstream path expected by HR agent: /interview/hr/{session_id}
                const targetUrl = `ws://hr-interview-agent:8009/interview/hr/${sessionId}${query ? '?' + query : ''}`;

                // Predăm conexiunea către WebSocket
                return handleProxy(request, targetUrl);
            }

            // 2. Match pentru Tech Interview
            if (pathPart.startsWith('/ws/tech-interview/')) {
                const sessionId = pathPart.split('/').pop();
                // Upstream path expected by Tech agent: /interview/tech/{session_id}
                const targetUrl = `ws://technical-interview-agent:8010/interview/tech/${sessionId}${query ? '?' + query : ''}`;

                return handleProxy(request, targetUrl);
            }
        }
    });

    // Funcția care face tunelul efectiv
    function handleProxy(request: any, targetUrl: string) {
        // Accesăm socket-ul brut expus de @fastify/websocket
        const socket = request.server.websocketServer;

        socket.handleUpgrade(request.raw, request.raw.socket, Buffer.alloc(0), (connection) => {

            // Verificare Token (în query string)
            const token = request.query?.token || (() => {
                try {
                    if (!request.raw.url) return null;
                    const q = request.raw.url.split('?')[1] || '';
                    const params = new URLSearchParams(q);
                    return params.get('token');
                } catch {
                    return null;
                }
            })();

            if (!token) {
                console.warn('WebSocket connection attempt without token');
                connection.close(1008, 'Token missing');
                return;
            }

            console.log(`Proxying WS to: ${targetUrl}`);
            const upstreamSocket = new WebSocket(targetUrl);

            // Client -> Agent
            // Preserve frame type: text frames must stay text (agenții fac
            // websocket.receive_text() și pică pe binary frame).
            connection.on('message', (message: any, isBinary: boolean) => {
                if (upstreamSocket.readyState === WebSocket.OPEN) {
                    upstreamSocket.send(message, { binary: isBinary });
                }
            });

            // Agent -> Client
            upstreamSocket.on('message', (message: any, isBinary: boolean) => {
                if (connection.readyState === WebSocket.OPEN) {
                    connection.send(message, { binary: isBinary });
                }
            });

            // Error handling & Cleanup
            upstreamSocket.on('close', (code: number, reason: any) => {
                try { connection.close(code, reason?.toString?.() ?? ''); } catch {};
            });

            connection.on('close', (code: number, reason: any) => {
                try { upstreamSocket.close(code, reason?.toString?.() ?? ''); } catch {};
            });

            upstreamSocket.on('error', () => {
                try { connection.close(1011, 'Upstream error'); } catch {};
            });
        });
    }
}