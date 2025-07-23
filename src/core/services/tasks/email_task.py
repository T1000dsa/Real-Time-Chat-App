import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from typing import Optional

from src.core.services.tasks.celery_app import app
from src.core.config.config import settings


logger = logging.getLogger(__name__)

@app.task(max_retries=3)
def send_email_task(recipient: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """Celery task for sending emails"""
    logger.debug('in celery task send_email_task')
    try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = settings.email.EMAIL_FROM.get_secret_value()
            msg['To'] = recipient

            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)

            with smtplib.SMTP(
                host=settings.email.EMAIL_HOST,
                port=settings.email.EMAIL_PORT,
                timeout=settings.email.EMAIL_TIMEOUT
            ) as server:
                if settings.email.EMAIL_USE_TLS:
                    server.starttls()
                server.login(
                    settings.email.EMAIL_USERNAME.get_secret_value(),
                    settings.email.EMAIL_PASSWORD.get_secret_value()
                )
                server.send_message(msg)
                logger.debug('Message was sent to the email')

            return True
    except Exception as e:
        logger.error(f"Email failed: {str(e)}")
        return False