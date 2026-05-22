import os

GAME_VERSION   = "1.1.0"
INSTALLER_WIN  = "Reconquest_Setup_v1.0.0.exe"
INSTALLER_LNX  = "Reconquest_Setup_v1.0.0.sh"
INSTALLER_URL_WIN = "https://github.com/XabierUrrutia/Reconquest_Web/releases/download/v1.1.0/Reconquest_Setup_v1.1.0.exe"
INSTALLER_URL_LNX = "https://github.com/XabierUrrutia/Reconquest_Web/releases/download/v1.1.0/Reconquest_Setup_v1.1.0.sh"
INSTALLER_NAME = INSTALLER_WIN
INSTALLER_URL  = INSTALLER_URL_WIN

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY", "")
SITE_URL         = os.environ.get("SITE_URL", "http://localhost:5000")

DATABASE_URL = os.environ.get("DATABASE_URL", "")
