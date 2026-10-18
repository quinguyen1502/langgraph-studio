"""SMTP sending shared by notification and password reset e-mail (TASK-0045). Settings: `config.smtp()`."""
import smtplib, ssl
from email.message import EmailMessage
from typing import Optional
from ..core.logging import get_logger

log = get_logger("mail")


def send(smtp: dict, to: str, subject: str, text: str, html: Optional[str] = None) -> bool:
    """Send one message; False (logged, no exception) when the server refuses or is unreachable."""
    msg = EmailMessage(); msg["From"] = smtp["sender"]; msg["To"] = to; msg["Subject"] = subject
    msg.set_content(text)
    if html: msg.add_alternative(html, subtype="html")
    try:
        cls = smtplib.SMTP_SSL if smtp["ssl"] else smtplib.SMTP
        with cls(smtp["host"], smtp["port"], timeout=10) as s:
            if smtp["starttls"] and not smtp["ssl"]:
                s.ehlo()
                if s.has_extn("starttls"): s.starttls(context=ssl.create_default_context()); s.ehlo()
            if smtp["user"]: s.login(smtp["user"], smtp["password"] or "")
            s.send_message(msg)
        return True
    except (OSError, smtplib.SMTPException) as e:
        log.warning("e-mail failed: %s", type(e).__name__); return False
