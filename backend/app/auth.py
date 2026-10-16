import hashlib, hmac, logging, os, re, secrets, time
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

log = logging.getLogger("studio.auth")
PLACEHOLDER_SECRET = "dev-secret-change-me"
SECRET = os.environ.get("JWT_SECRET", PLACEHOLDER_SECRET)
TTL = int(os.environ.get("JWT_TTL_SECONDS", 60 * 60 * 24))
ITER = 200_000
IS_PROD = os.environ.get("STUDIO_ENV", "dev").lower() in ("prod", "production")

def check_secret():
    """Refuse the placeholder secret in production; warn in dev."""
    if SECRET == PLACEHOLDER_SECRET:
        if IS_PROD: raise RuntimeError("JWT_SECRET must be set when STUDIO_ENV=production")
        log.warning("JWT_SECRET is the development placeholder; set JWT_SECRET before deploying")
        return False
    return True

def password_problem(pw: str) -> str | None:
    """Return a user-facing message if the password is too weak, else None."""
    if len(pw) < 8: return "Mật khẩu phải có ít nhất 8 ký tự"
    if len(pw) > 128: return "Mật khẩu tối đa 128 ký tự"
    if not re.search(r"[A-Za-z]", pw) or not re.search(r"\d", pw): return "Mật khẩu phải có cả chữ và số"
    return None

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

def make_token(uid: str, email: str, ttl: int | None = None) -> str:
    return jwt.encode({"sub": uid, "email": email, "exp": int(time.time()) + (TTL if ttl is None else ttl)}, SECRET, algorithm="HS256")

def decode_token(tok: str) -> dict:
    try:
        return jwt.decode(tok, SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Phiên đăng nhập đã hết hạn", headers={"X-Auth-Error": "expired"})
    except jwt.PyJWTError:
        raise HTTPException(401, "Token không hợp lệ hoặc đã hết hạn")

bearer = HTTPBearer(auto_error=False)
def current_user(cred: HTTPAuthorizationCredentials | None = Depends(bearer)) -> dict:
    if not cred: raise HTTPException(401, "Chưa đăng nhập")
    p = decode_token(cred.credentials)
    return {"id": p["sub"], "email": p["email"]}
