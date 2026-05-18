import hashlib
from datetime import datetime


def _now():
    return datetime.utcnow().isoformat()


def _hash_pwd(password, salt):
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()


def detect_client_os(user_agent_str):
    """Detecta el SO del cliente a partir del User-Agent.
    Devuelve: 'windows', 'linux', 'mac', 'android', 'ios' o 'unknown'.
    """
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
