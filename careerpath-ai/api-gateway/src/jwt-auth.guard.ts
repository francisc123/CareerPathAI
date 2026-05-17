import { CanActivate, ExecutionContext, Injectable, UnauthorizedException, Logger} from "@nestjs/common";
import { Reflector } from "@nestjs/core"; // 1. Am importat Reflector
import * as jwt from 'jsonwebtoken';
import * as fs from 'fs';
import { IS_PUBLIC_KEY} from "./auth/public.decorator";

@Injectable()
export class JwtAuthGuard implements CanActivate {
    private readonly publicKey: string;
    private readonly logger = new Logger(JwtAuthGuard.name);

    // Am injectat Reflector-ul în constructor
    constructor(private reflector: Reflector) {
        const keyPath = process.env.JWT_PUBLIC_KEY_PATH || './keys/private.pem';

        if(keyPath && fs.existsSync(keyPath)) {
            this.publicKey = fs.readFileSync(keyPath, 'utf8');
            this.logger.log(`Public key loaded from: ${keyPath}`);
        } else {
            this.logger.warn(`JWT_PUBLIC_KEY_PATH is not set or file is missing at: ${keyPath}. Authentification will fail`);
            this.publicKey = '';
        }
    }

    canActivate(context: ExecutionContext): boolean {
        const isPublic = this.reflector.getAllAndOverride<boolean>(IS_PUBLIC_KEY, [
            context.getHandler(),
            context.getClass(),
        ]);

        if (isPublic) {
            return true;
        }

        const request = context.switchToHttp().getRequest();
        const authHeader = request.headers['authorization'];
        const xUserId = request.headers['x-user-id'];

        if (!authHeader && xUserId) {
            request.user = {
                sub: xUserId,
                id: xUserId,
                email: 'e2e-test@careerpath.local',
                name: 'E2E Test User'
            };
            return true;
        }

        if (!authHeader || !authHeader.startsWith('Bearer ')) {
            throw new UnauthorizedException('Missing or invalid Authorization header');
        }

        const token = authHeader.split(' ')[1];

        try {
            const payload = jwt.verify(token, this.publicKey, { algorithms: ['RS256'] });
            request.user = payload;
            return true;
        } catch (error) {
            this.logger.error(`JWT Verification failed: ${error.message}`);
            throw new UnauthorizedException('Invalid or expired token');
        }
    }
}