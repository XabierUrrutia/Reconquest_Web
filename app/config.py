import os

GAME_VERSION   = "1.0.0"
INSTALLER_WIN  = "Reconquest_Setup_v1.0.0.exe"
INSTALLER_LNX  = "Reconquest_Setup_v1.0.0.sh"
INSTALLER_URL_WIN = "https://github.com/XabierUrrutia/Renconquest_Web/releases/download/v1.0.0/Reconquest_Setup_v1.0.0.exe"
INSTALLER_URL_LNX = "https://github.com/XabierUrrutia/Renconquest_Web/releases/download/v1.0.0/Reconquest_Setup_v1.0.0.sh"

INSTALLER_NAME = INSTALLER_WIN
INSTALLER_URL  = INSTALLER_URL_WIN

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

SMTP_HOST  = os.environ.get("SMTP_HOST",  "smtp.gmail.com")
SMTP_PORT  = int(os.environ.get("SMTP_PORT", 587))
SMTP_USER  = os.environ.get("SMTP_USER",  "")
SMTP_PASS  = os.environ.get("SMTP_PASS",  "")
SITE_URL   = os.environ.get("SITE_URL",   "http://localhost:5000")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
