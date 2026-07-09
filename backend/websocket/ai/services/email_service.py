import smtplib
import os
import logging
from email.message import EmailMessage

logger = logging.getLogger(__name__)

def send_otp_email(to_email: str, otp: str):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_EMAIL", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    msg_content = f"""
    Hello,

    You requested a password reset for your Teacher AI account.
    Your One-Time Password (OTP) is: {otp}

    This OTP will expire in 10 minutes.
    If you did not request this, please ignore this email.

    Thank you,
    Teacher AI Team
    """

    if not smtp_user or not smtp_pass:
        # Fallback for dev environments if SMTP isn't configured
        logger.warning(f"SMTP not configured. Mocking email to {to_email}. OTP: {otp}")
        print("\n========== MOCK EMAIL ==========")
        print(f"To: {to_email}")
        print(f"OTP: {otp}")
        print("================================\n")
        return True

    msg = EmailMessage()
    msg.set_content(msg_content)
    msg['Subject'] = 'Password Reset OTP'
    msg['From'] = smtp_user
    msg['To'] = to_email

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        logger.info(f"OTP email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise e
