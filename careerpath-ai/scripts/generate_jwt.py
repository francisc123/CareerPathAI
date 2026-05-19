import sys, os, json, time
from base64 import urlsafe_b64encode
from hashlib import sha256
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

# Minimal base64url without padding
def b64u(data: bytes) -> str:
    return urlsafe_b64encode(data).rstrip(b"=").decode('utf-8')

key_path = os.environ.get('PRIVATE_KEY_PATH', './keys/private.pem')
if not os.path.exists(key_path):
    print(f'Private key not found at {key_path}', file=sys.stderr)
    sys.exit(2)

with open(key_path,'rb') as f:
    private_bytes = f.read()

private_key = serialization.load_pem_private_key(private_bytes, password=None)

now = int(time.time())
payload = {
    'sub': os.environ.get('TEST_JWT_SUB','test-user'),
    'iss': os.environ.get('TEST_JWT_ISS','careerpath-ai-test'),
    'iat': now,
    'exp': now + int(os.environ.get('TEST_JWT_EXP_SECONDS','3600'))
}
header = { 'alg': 'RS256', 'typ': 'JWT' }

header_b64 = b64u(json.dumps(header, separators=(',',':')).encode('utf-8'))
payload_b64 = b64u(json.dumps(payload, separators=(',',':')).encode('utf-8'))
signing_input = f"{header_b64}.{payload_b64}".encode('utf-8')

signature = private_key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
sig_b64 = b64u(signature)

print(f"{header_b64}.{payload_b64}.{sig_b64}")

