import hashlib
import bcrypt
from datetime import datetime


def _now():
    return datetime.utcnow().isoformat()


def _hash_pwd(password: str) -> str:
    """Hash a password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _check_pwd(password: str, stored_hash: str, legacy_salt: str = "") -> bool:
    """Verify a password against a stored hash (bcrypt or legacy SHA256)."""
    if stored_hash.startswith(("$2b$", "$2a$")):
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    return hashlib.sha256(f"{legacy_salt}{password}".encode()).hexdigest() == stored_hash


def _is_legacy_hash(stored_hash: str) -> bool:
    return not stored_hash.startswith(("$2b$", "$2a$"))


def detect_client_os(user_agent_str):
    ua = (user_agent_str or "").lower()
    if "iphone" in ua or "ipad" in ua or "ipod" in ua:
        return "ios"
    if "android" in ua:
        return "android"
    if "windows" in ua:
        return "windows"
    if "macintosh" in ua or "mac os" in ua:
        return "mac"
    if "linux" in ua or "x11" in ua:
        return "linux"
    return "unknown"


def is_mobile(client_os):
    return client_os in ("android", "ios")
