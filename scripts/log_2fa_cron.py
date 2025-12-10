#!/usr/bin/env python3
from datetime import datetime, timezone
from pathlib import Path
import sys
import base64
import pyotp

DATA_PATH = Path("/data/seed.txt")
OUT_PATH = Path("/cron/last_code.txt")

def utc_now_str():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

try:
    if not DATA_PATH.exists():
        print(f"{utc_now_str()} ERROR: seed not found", file=sys.stderr)
        sys.exit(1)
    hex_seed = DATA_PATH.read_text(encoding="utf-8").strip()
    if len(hex_seed) != 64:
        print(f"{utc_now_str()} ERROR: invalid seed length", file=sys.stderr)
        sys.exit(1)
    seed_bytes = bytes.fromhex(hex_seed)
    b32 = base64.b32encode(seed_bytes).decode("utf-8")
    totp = pyotp.TOTP(b32, digits=6, interval=30)
    code = totp.now()
    line = f"{utc_now_str()} 2FA Code: {code}"
    print(line)
    with OUT_PATH.open("a", encoding="utf-8") as f:
        f.write(line + "\\n")
except Exception as e:
    print(f"{utc_now_str()} EXCEPTION: {e}", file=sys.stderr)
    sys.exit(1)
