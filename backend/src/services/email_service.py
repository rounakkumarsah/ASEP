"""
ASEP — Email Service (Resend SDK Implementation)
"""

import logging
from src.config.settings import get_settings
from src.services.audit_service import AuditService
from src.db.models.audit_log import ActorType, AuditOutcome, AuditSeverity

logger = logging.getLogger(__name__)

# Base HTML wrapper for emails with professional ASEP branding
HTML_TEMPLATE_WRAPPER = """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      background-color: #0b0f19;
      color: #f3f4f6;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
    }}
    .wrapper {{
      padding: 40px 20px;
      max-width: 600px;
      margin: 0 auto;
    }}
    .card {{
      background-color: #111827;
      border: 1px solid #1f2937;
      border-radius: 8px;
      padding: 32px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }}
    .logo {{
      display: flex;
      align-items: center;
      margin-bottom: 24px;
      color: #10b981;
      font-size: 24px;
      font-weight: bold;
      letter-spacing: -0.025em;
    }}
    .title {{
      font-size: 20px;
      font-weight: 700;
      margin-bottom: 16px;
      color: #ffffff;
    }}
    .content {{
      font-size: 16px;
      line-height: 24px;
      color: #d1d5db;
      margin-bottom: 24px;
    }}
    .btn {{
      display: inline-block;
      background-color: #10b981;
      color: #0b0f19 !important;
      font-weight: 600;
      padding: 12px 24px;
      border-radius: 6px;
      text-decoration: none;
      font-size: 16px;
      text-align: center;
      margin: 24px 0;
    }}
    .footer {{
      font-size: 12px;
      color: #6b7280;
      text-align: center;
      margin-top: 32px;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="card">
      <div class="logo">ASEP</div>
      {CONTENT}
    </div>
    <div class="footer">
      &copy; 2026 ASEP. All rights reserved.<br>
      Autonomous Software Engineering Platform
    </div>
  </div>
</body>
</html>
"""


class EmailService:
    """Production email delivery service using the official Resend Python SDK."""

    def __init__(self, audit_service: AuditService) -> None:
        import os
        self.audit_service = audit_service
        self.settings = get_settings()
        self.api_key = os.getenv("RESEND_API_KEY") or self.settings.RESEND_API_KEY
        
        # Configure the Resend SDK
        if self.api_key and self.api_key not in ("mock", "", "None"):
            try:
                import resend
                resend.api_key = self.api_key
            except ImportError:
                logger.warning("Resend SDK not installed. Falling back to mock email delivery.")
                self.api_key = "mock"

    async def _send_email(self, to_email: str, subject: str, html_content: str, email_type: str) -> bool:
        """Deliver email using Resend SDK or mock delivery locally with robust retry logic."""
        to_email = to_email.strip().lower()

        # If API key is missing or mock, simulate delivery and write to audit logs
        if not self.api_key or self.api_key in ("mock", "", "None"):
            logger.info(f"Email sent: [MOCK SDK EMAIL] To: {to_email} | Type: {email_type} | Subject: {subject}")
            
            # Audit log mock delivery
            await self.audit_service.log_event(
                actor_type=ActorType.SYSTEM,
                actor_id="system.email_service",
                action=f"email.{email_type}_sent_mock",
                resource_type="email",
                outcome=AuditOutcome.SUCCESS,
                severity=AuditSeverity.INFO,
                log_details={"to": to_email, "subject": subject}
            )
            return True

        from_address = self.settings.EMAIL_FROM
        if from_address == "noreply@asep.local" or not from_address:
            from_address = "onboarding@resend.dev"

        params = {
            "from": f"ASEP <{from_address}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }

        max_retries = 3
        import asyncio
        for attempt in range(1, max_retries + 1):
            try:
                # Send email via Resend SDK in thread pool to avoid blocking
                import resend
                response = await asyncio.to_thread(resend.Emails.send, params)
                
                logger.info(f"Email sent: SDK Email {email_type} successfully sent to {to_email} on attempt {attempt}")
                await self.audit_service.log_event(
                    actor_type=ActorType.SYSTEM,
                    actor_id="system.email_service",
                    action=f"email.{email_type}_sent",
                    resource_type="email",
                    outcome=AuditOutcome.SUCCESS,
                    severity=AuditSeverity.INFO,
                    log_details={"to": to_email, "subject": subject, "resend_id": getattr(response, "id", None)}
                )
                return True
            except Exception as e:
                err_msg = str(e).lower()
                is_invalid_key = "unauthorized" in err_msg or "api key" in err_msg or "invalid" in err_msg
                
                if attempt < max_retries and not is_invalid_key:
                    logger.warning(f"Retry: Failed to send {email_type} email to {to_email} (attempt {attempt}/{max_retries}): {e}")
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"Email failed: Failed to send {email_type} email to {to_email} after {attempt} attempts: {e}")
                    await self.audit_service.log_event(
                        actor_type=ActorType.SYSTEM,
                        actor_id="system.email_service",
                        action=f"email.{email_type}_failed",
                        resource_type="email",
                        outcome=AuditOutcome.FAILURE,
                        severity=AuditSeverity.ERROR,
                        log_details={"to": to_email, "subject": subject, "error": str(e)}
                    )
                    return False
        return False

    async def send_verification_email(self, email: str, username: str, verification_token: str) -> bool:
        """Send verification email link."""
        verify_link = f"{self.settings.FRONTEND_URL}/verify-email?token={verification_token}"
        content = f"""
        <div class="title">Verify your ASEP account</div>
        <div class="content">
          Hi {username},<br><br>
          Thank you for signing up for ASEP. Please click the button below to verify your email address and activate your account:
        </div>
        <div style="text-align: center;">
          <a href="{verify_link}" class="btn">Verify Account</a>
        </div>
        <div class="content" style="font-size: 14px; color: #9ca3af; margin-top: 16px;">
          Or copy and paste this link in your browser:<br>
          <a href="{verify_link}" style="color: #10b981;">{verify_link}</a>
        </div>
        """
        html = HTML_TEMPLATE_WRAPPER.format(CONTENT=content)
        return await self._send_email(email, "Verify your ASEP account", html, "verify")

    async def send_welcome_email(self, to_email: str, name: str) -> bool:
        """Send a welcome email upon successful account verification/signup."""
        login_link = f"{self.settings.FRONTEND_URL}/login"
        content = f"""
        <div class="title">Welcome to ASEP</div>
        <div class="content">
          Hi {name},<br><br>
          Your email address has been successfully verified. Welcome to the Autonomous Software Engineering Platform!<br><br>
          Click the button below to access your dashboard and start orchestrating your engineering workspaces:
        </div>
        <div style="text-align: center;">
          <a href="{login_link}" class="btn">Launch Dashboard</a>
        </div>
        """
        html = HTML_TEMPLATE_WRAPPER.format(CONTENT=content)
        return await self._send_email(to_email, "Welcome to ASEP", html, "welcome")

    async def send_reset_password_email(self, to_email: str, token: str) -> bool:
        """Send forgot password reset token email link."""
        reset_link = f"{self.settings.FRONTEND_URL}/reset-password?token={token}"
        content = f"""
        <div class="title">Reset your password</div>
        <div class="content">
          We received a request to reset the password associated with your account. Click the button below to set a new password:
        </div>
        <div style="text-align: center;">
          <a href="{reset_link}" class="btn">Reset Password</a>
        </div>
        <div class="content" style="font-size: 14px; color: #9ca3af; margin-top: 16px;">
          If you did not request a password reset, you can safely ignore this email.
        </div>
        """
        html = HTML_TEMPLATE_WRAPPER.format(CONTENT=content)
        return await self._send_email(to_email, "Reset your password", html, "forgot_password")
    
    async def send_resend_verification_email(self, email: str, username_or_code: str, code: str | None = None) -> bool:
        """Resend verification code email."""
        actual_code = code if code is not None else username_or_code
        content = f"""
        <div class="title">Your verification code</div>
        <div class="content">
          Here is your new verification code:<br><br>
          <strong style="font-size: 24px; letter-spacing: 4px;">{actual_code}</strong>
        </div>
        """
        html = HTML_TEMPLATE_WRAPPER.format(CONTENT=content)
        return await self._send_email(email, "Your ASEP verification code", html, "resend_verification")
    
    async def send_password_changed_email(self, to_email: str) -> bool:
        """Send confirmation email after password change."""
        content = """
        <div class="title">Password Changed</div>
        <div class="content">
          Your ASEP account password has been successfully changed. If you did not make this change, please contact support immediately.
        </div>
        """
        html = HTML_TEMPLATE_WRAPPER.format(CONTENT=content)
        return await self._send_email(to_email, "Your password has been changed", html, "password_changed")
