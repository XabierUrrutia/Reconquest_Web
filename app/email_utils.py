import resend
from flask import current_app

from .config import RESEND_API_KEY, SITE_URL


def send_reset_email(to_email, token):
    if not RESEND_API_KEY:
        current_app.logger.warning("RESEND_API_KEY not configured. Password reset email could not be sent.")
        return False
    try:
        resend.api_key = RESEND_API_KEY
        link = f"{SITE_URL}/reset/{token}"
        resend.Emails.send({
            "from": "Reconquest <onboarding@resend.dev>",
            "to": to_email,
            "subject": "Reconquest — Restablecer contraseña",
            "text": (
                f"Hola,\n\nRestablece tu contraseña de Reconquest en este enlace (válido 1 hora):\n\n"
                f"{link}\n\nSi no lo solicitaste, ignora este correo.\n\n— Equipo Reconquest"
            ),
        })
        return True
    except Exception as e:
        current_app.logger.error("Email error: %s", e)
        return False
