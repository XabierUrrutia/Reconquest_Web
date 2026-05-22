from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from flask import current_app

from .config import SENDGRID_API_KEY, SITE_URL

SENDER_EMAIL = "bugfactory373@gmail.com"


def send_reset_email(to_email, token):
    if not SENDGRID_API_KEY:
        current_app.logger.warning("SENDGRID_API_KEY not configured. Password reset email could not be sent.")
        return False
    try:
        link = f"{SITE_URL}/reset/{token}"
        message = Mail(
            from_email=SENDER_EMAIL,
            to_emails=to_email,
            subject="Reconquest — Restablecer contraseña",
            plain_text_content=(
                f"Hola,\n\nRestablece tu contraseña de Reconquest en este enlace (válido 1 hora):\n\n"
                f"{link}\n\nSi no lo solicitaste, ignora este correo.\n\n— Equipo Reconquest"
            ),
        )
        SendGridAPIClient(SENDGRID_API_KEY).send(message)
        return True
    except Exception as e:
        current_app.logger.error("Email error: %s", e)
        return False
