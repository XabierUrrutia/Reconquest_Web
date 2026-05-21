import smtplib
from email.mime.text import MIMEText
from flask import current_app

from .config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SITE_URL


def send_reset_email(to_email, token):
    if not SMTP_USER:
        current_app.logger.warning("SMTP not configured. Reset link: %s/reset/%s", SITE_URL, token)
        return False
    try:
        link = f"{SITE_URL}/reset/{token}"
        msg  = MIMEText(
            f"Hola,\n\nRestablece tu contraseña de Reconquest en este enlace (válido 1 hora):\n\n"
            f"{link}\n\nSi no lo solicitaste, ignora este correo.\n\n— Equipo Reconquest",
            "plain", "utf-8"
        )
        msg["Subject"] = "Reconquest — Restablecer contraseña"
        msg["From"]    = SMTP_USER
        msg["To"]      = to_email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_USER, to_email, msg.as_string())
        return True
    except Exception as e:
        current_app.logger.error("Email error: %s", e)
        return False
