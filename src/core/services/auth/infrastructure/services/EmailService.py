from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import smtplib
import logging

from src.core.services.auth.domain.interfaces import EmailRepo
from src.utils.time_check import time_checker
from src.core.config.config import settings, EXTERNAL_BASE_URL, main_prefix
from src.core.services.auth.domain.models.user import UserModel
from src.core.services.auth.infrastructure.services.User_Crud import UserService
from src.core.services.tasks.email_task import send_email_task

logger = logging.getLogger(__name__)

class EmailService(EmailRepo):
    def __init__(self):
        self.settings = settings.email

    def _send_email_sync(self, recipient: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Core email-sending logic (sync version for Celery)"""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.settings.EMAIL_FROM.get_secret_value()
            msg['To'] = recipient

            part1 = MIMEText(body, 'plain')
            msg.attach(part1)
            if html_body:
                part2 = MIMEText(html_body, 'html')
                msg.attach(part2)

            with smtplib.SMTP(
                host=self.settings.EMAIL_HOST,
                port=self.settings.EMAIL_PORT,
                timeout=self.settings.EMAIL_TIMEOUT
            ) as server:
                if self.settings.EMAIL_USE_TLS:
                    server.starttls()
                server.login(
                    self.settings.EMAIL_USERNAME.get_secret_value(),
                    self.settings.EMAIL_PASSWORD.get_secret_value()
                )
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Email failed: {str(e)}")
            return False

    @time_checker
    async def send_email(self, recipient: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Public API now delegates to TaskIQ"""
        if not self.settings.EMAIL_ENABLED:
            logger.warning("Email sending disabled in settings")
            return False

        # Fire-and-forget TaskIQ task (no need to wait for result)
        logger.debug("Before taskiq task")
        await send_email_task.kiq(recipient, subject, body, html_body)
        return True  # Assume success since we're firing and forgetting

    # Other methods remain the same...
    @time_checker
    async def send_verification_email(self, recipient: str) -> bool:
        verification_url = f"{EXTERNAL_BASE_URL}{main_prefix}/verify_email"
        subject = "Please verify your email address"
        body = f"Click this link to verify your email: {verification_url}"
        html_body = f"""<html><body><p>Click <a href="{verification_url}">here</a> to verify.</p></body></html>"""
        return await self.send_email(recipient, subject, body, html_body)
    
    @time_checker
    async def send_generated_qrcode(self, recipient: str, image_link: str) -> bool:

        subject = "Please scan this QR code"
        body = f"Scan this QR code for MFA for {EXTERNAL_BASE_URL}"
        
        # Create proper HTML with embedded image
        html_body = f"""
        <html>
            <body>
                <a href="{image_link}">Link to the qr code</a>
            </body>
        </html>
        """
        logger.debug(f"{html_body=}")
        
        return await self.send_email(recipient, subject, body, html_body)
    
    async def email_verification(self, session: AsyncSession, email: str,  user_repo: UserService, user: Optional[UserModel] = None):
        email_user = await user_repo.get_user_for_auth_by_email(session, email)
        logger.debug(f'{email_user} {user}')
        if user and email_user:
            if email_user.id != user.id:
                raise KeyError('User email and provided email not matched! Please provide YOUR email!')
        else:
            if email_user is None:
                raise KeyError("Such email doesnt exist!")