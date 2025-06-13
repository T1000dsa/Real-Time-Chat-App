from typing import Optional

from src.core.services.tasks.celery import celery
from src.core.services.auth.infrastructure.services.EmailService import EmailService


@celery.task(bind=True, max_retries=3)
def send_email_task(self, recipient: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    """Celery task for sending emails"""
    email_service = EmailService()
    return email_service._send_email_sync(recipient, subject, body, html_body)