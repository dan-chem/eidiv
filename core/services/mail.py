# core/services/mail.py
from typing import Iterable, Optional, Sequence
from django.conf import settings
from django.core.mail import EmailMessage, get_connection
from core.models import MailEmpfaenger

def get_active_recipients() -> list[str]:
    return list(MailEmpfaenger.objects.filter(aktiv=True).values_list("email", flat=True))

def send_mail_text(
    subject: str,
    body_text: str,
    to: Optional[Sequence[str]] = None,
    bcc: Optional[Sequence[str]] = None,
    from_email: Optional[str] = None,
    attachments: Optional[Iterable[tuple[str, bytes, str]]] = None,
    headers: Optional[dict] = None,
    fail_silently: bool = False,
) -> int:
    from_email = from_email or settings.DEFAULT_FROM_EMAIL
    conn = get_connection(timeout=getattr(settings, "EMAIL_TIMEOUT", None))
    msg = EmailMessage(
        subject=f"{getattr(settings,'EMAIL_SUBJECT_PREFIX','')}{subject}".strip(),
        body=body_text,
        from_email=from_email,
        to=list(to or []),
        bcc=list(bcc or []),
        headers=headers or {},
        connection=conn,
    )
    if attachments:
        for name, data, mime in attachments:
            msg.attach(name, data, mime)
    return msg.send(fail_silently=fail_silently)

def send_mail_with_pdf_to_active(
    subject: str,
    body_text: str,
    pdf_bytes: bytes,
    filename: str,
    use_bcc: bool = True,
    fail_silently: bool = False,
) -> int:
    recipients = get_active_recipients()
    if not recipients:
        return 0
    to = recipients if not use_bcc else []
    bcc = recipients if use_bcc else []
    return send_mail_text(
        subject=subject,
        body_text=body_text,
        to=to,
        bcc=bcc,
        attachments=[(filename, pdf_bytes, "application/pdf")],
        fail_silently=fail_silently,
    )
