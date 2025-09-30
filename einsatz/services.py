# einsatz/services.py
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.core.mail import EmailMessage
from weasyprint import HTML, CSS
from django.contrib.staticfiles import finders

from core.models import MailEmpfaenger


def assign_running_number(instance, model_cls):
    """
    Vergibt eine laufende Nummer pro Jahr (seq) transaktional.
    model_cls ist die Modelklasse (z. B. Einsatz).
    """
    if getattr(instance, "year", None) and getattr(instance, "seq", None):
        return
    with transaction.atomic():
        year = timezone.now().year
        max_seq = model_cls.objects.select_for_update().filter(year=year).aggregate(Max("seq"))["seq__max"] or 0
        instance.year = year
        instance.seq = max_seq + 1


def render_html_to_pdf_bytes(html: str, base_url=None, extra_css_paths: list[str] | None = None) -> bytes:
    stylesheets = []

    # print.css aus dem Static-Finder holen (funktioniert auch in Prod nach collectstatic)
    css_path = finders.find('css/print.css')
    if css_path:
        stylesheets.append(CSS(filename=css_path))

    # optional weitere lokale CSS-Pfade akzeptieren
    if extra_css_paths:
        for p in extra_css_paths:
            if p:
                stylesheets.append(CSS(filename=p))

    return HTML(string=html, base_url=base_url).write_pdf(stylesheets=stylesheets)


def send_mail_with_pdf(subject, body_text, pdf_bytes, filename):
    recipients = list(MailEmpfaenger.objects.filter(aktiv=True).values_list("email", flat=True))
    if not recipients:
        return 0
    msg = EmailMessage(subject=subject, body=body_text, to=recipients)
    msg.attach(filename, pdf_bytes, "application/pdf")
    return msg.send(fail_silently=True)

