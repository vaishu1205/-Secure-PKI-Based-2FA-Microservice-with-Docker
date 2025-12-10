from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64
import os
import time
import pyotp

app = FastAPI()
DATA_DIR = Path('/data')
SEED_PATH = DATA_DIR / 'seed.txt'
PRIVATE_KEY_PATH = Path('student_private.pem')

class DecryptRequest(BaseModel):
    encrypted_seed: str

class VerifyRequest(BaseModel):
    code: str

def load_private_key(path: Path):
    if not path.exists():
        raise FileNotFoundError('private key not found')
    data = path.read_bytes()
    return serialization.load_pem_private_key(data, password=None)

def decrypt_seed_b64(encrypted_b64: str, private_key) -> str:
    try:
        ct = base64.b64decode(encrypted_b64)
    except Exception:
        raise ValueError('invalid base64')
    try:
        pt = private_key.decrypt(
            ct,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
    except Exception:
        raise ValueError('decryption failed')
    try:
        s = pt.decode('utf-8').strip()
    except Exception:
        raise ValueError('invalid plaintext encoding')
    if len(s) != 64:
        raise ValueError('seed length invalid')
    try:
        int(s, 16)
    except Exception:
        raise ValueError('seed not hex')
    return s.lower()

def persist_seed(hex_seed: str):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEED_PATH.write_text(hex_seed, encoding='utf-8')
    try:
        os.chmod(SEED_PATH, 0o600)
    except Exception:
        # non-fatal on platforms that don't support Unix perms
        pass


def read_seed() -> str:
    if not SEED_PATH.exists():
        raise FileNotFoundError('seed not found')
    s = SEED_PATH.read_text(encoding='utf-8').strip()
    if len(s) != 64:
        raise ValueError('invalid seed stored')
    return s

def hex_to_base32(hex_seed: str) -> str:
    b = bytes.fromhex(hex_seed)
    return base64.b32encode(b).decode('utf-8')

@app.post('/decrypt-seed')
async def decrypt_seed(req: DecryptRequest):
    try:
        private_key = load_private_key(PRIVATE_KEY_PATH)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail={'error': 'Private key not found'})
    try:
        hex_seed = decrypt_seed_b64(req.encrypted_seed, private_key)
    except ValueError as e:
        raise HTTPException(status_code=500, detail={'error': 'Decryption failed'})
    try:
        persist_seed(hex_seed)
    except Exception:
        raise HTTPException(status_code=500, detail={'error': 'Failed to persist seed'})
    return {'status': 'ok'}

@app.get('/generate-2fa')
async def generate_2fa():
    try:
        hex_seed = read_seed()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail={'error': 'Seed not decrypted yet'})
    except Exception:
        raise HTTPException(status_code=500, detail={'error': 'Seed invalid'})
    b32 = hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    code = totp.now()
    period = 30
    epoch = int(time.time())
    valid_for = period - (epoch % period)
    return {'code': code, 'valid_for': valid_for}

@app.post('/verify-2fa')
async def verify_2fa(req: VerifyRequest):
    if not req.code:
        raise HTTPException(status_code=400, detail={'error': 'Missing code'})
    try:
        hex_seed = read_seed()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail={'error': 'Seed not decrypted yet'})
    except Exception:
        raise HTTPException(status_code=500, detail={'error': 'Seed invalid'})
    b32 = hex_to_base32(hex_seed)
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    valid = totp.verify(req.code, valid_window=1)
    return {'valid': bool(valid)}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='0.0.0.0', port=8080, log_level='info')
