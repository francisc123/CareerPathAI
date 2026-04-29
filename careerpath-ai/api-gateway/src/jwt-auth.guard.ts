import { CanActivate, ExecutionContext, Injectable, UnauthorizedException, Logger} from "@nestjs/common";
import * as jwt from 'jsonwebtoken';
import * as fs from 'fs';

@Injectable()
export class JwtAuthGuard implements CanActivate {
    private readonly publicKey: string;
    private readonly logger = new Logger(JwtAuthGuard.name);

    constructor() {
        const keyPath = process.env.JWT_PUBLIC_KEY_PATH;

        if(keyPath && fs.existsSync(keyPath)) {
            this.publicKey = fs.readFileSync(keyPath, 'utf8');
            this.logger.log(`Public key loaded from: ${keyPath}`);
        } else {
            this.logger.warn(`JWT_PUBLIC_KEY_PATH is not set or file is missing at: ${keyPath}. Authentification will fail`);
            this.publicKey = '';
        }
    }

    canActivate(context: ExecutionContext): boolean {
        const request = context.switchToHttp().getRequest();
        const authHeader = request.headers['authorization'];

        if(!authHeader || !authHeader.startsWith('Bearer ')) {
            throw new UnauthorizedException('Missing or invalid Authorization header');
        }
        const token = authHeader.split(' ')[1];

        try {
            const payload = jwt.verify(token, this.publicKey, {algorithms: ['RS256']});

            request.user = payload;
            return true;
        } catch (error) {
            this.logger.error(`JWT Verification failed: ${error.message}`);
            throw new UnauthorizedException('Invalid or expired token');
        }
    }
}