# einsatz/services.py
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.core.mail import EmailMessage
from core.models import MailEmpfaenger
from .models import Einsatz
from weasyprint import HTML

def assign_running_number(instance, model_cls):
    # instance is Einsatz or Dienst
    now = timezone.now()
    if getattr(instance, "year", None) and getattr(instance, "seq", None):
        return
    with transaction.atomic():
        year = now.year
        max_seq = model_cls.objects.select_for_update().filter(year=year).aggregate(Max("seq"))["seq__max"] or 0
        instance.year = year
        instance.seq = max_seq + 1

def send_mail_with_pdf(subject, body_text, pdf_bytes, filename):
    recipients = list(MailEmpfaenger.objects.filter(aktiv=True).values_list("email", flat=True))
    if not recipients:
        return 0
    msg = EmailMessage(
        subject=subject,
        body=body_text,
        to=recipients,
    )
    msg.attach(filename, pdf_bytes, "application/pdf")
    return msg.send(fail_silently=True)

def render_html_to_pdf_bytes(html):
    return HTML(string=html, base_url="").write_pdf()
