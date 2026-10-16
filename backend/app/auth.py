import hashlib, hmac, os, secrets, time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
TTL = 60 * 60 * 24
ITER = 200_000

def hash_password(pw: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), ITER).hex()
    return f"pbkdf2_sha256${ITER}${salt}${h}"

def verify_password(pw: str, stored: str) -> bool:
    try:
        _, it, salt, h = stored.split("$")
        return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), int(it)).hex(), h)
    except Exception:
        return False

def make_token(uid: str, email: str) -> str:
    return jwt.encode({"sub": uid, "email": email, "exp": int(time.time()) + TTL}, SECRET, algorithm="HS256")

def decode_token(tok: str) -> dict:
    try:
        return jwt.decode(tok, SECRET, algorithms=["HS256"])
    except jwt.PyJWTError:
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn")

bearer = HTTPBearer(auto_error=False)
def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not cred: raise HTTPException(401, "Chưa đăng nhập")
    p = decode_token(cred.credentials)
    return {"id": p["sub"], "email": p["email"]}
