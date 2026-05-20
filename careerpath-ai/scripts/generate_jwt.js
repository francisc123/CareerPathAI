const fs = require('fs');
const crypto = require('crypto');

function base64url(input) {
  if (Buffer.isBuffer(input)) return input.toString('base64url');
  return Buffer.from(String(input)).toString('base64url');
}

const header = { alg: 'RS256', typ: 'JWT' };
const now = Math.floor(Date.now()/1000);
const payload = {
  sub: process.env.TEST_JWT_SUB || 'test-user',
  iss: process.env.TEST_JWT_ISS || 'careerpath-ai-test',
  iat: now,
  exp: now + (process.env.TEST_JWT_EXP_SECONDS ? parseInt(process.env.TEST_JWT_EXP_SECONDS) : 3600)
};

const headerB64 = base64url(JSON.stringify(header));
const payloadB64 = base64url(JSON.stringify(payload));
const signingInput = `${headerB64}.${payloadB64}`;

const keyPath = process.env.PRIVATE_KEY_PATH || './keys/private.pem';
if (!fs.existsSync(keyPath)) {
  console.error(`Private key not found at ${keyPath}`);
  process.exit(2);
}
const privateKey = fs.readFileSync(keyPath, 'utf8');

const signer = crypto.createSign('RSA-SHA256');
signer.update(signingInput);
signer.end();
const signature = signer.sign(privateKey);
const signatureB64 = base64url(signature);

console.log(`${signingInput}.${signatureB64}`);

