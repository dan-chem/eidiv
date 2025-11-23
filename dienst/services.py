# dienst/services.py
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS

from .models import Dienst

def assign_running_number(instance):
    """
    Vergibt eine laufende Nummer pro Jahr (seq) transaktional – nur für Dienst.
    """
    if getattr(instance, "year", None) and getattr(instance, "seq", None):
        return
    with transaction.atomic():
        # Jahr aus start_dt ableiten, falls gesetzt
        year = None
        try:
            if getattr(instance, "start_dt", None):
                year = instance.start_dt.year
        except Exception:
            year = None
        if not year:
            year = timezone.now().year
        max_seq = Dienst.objects.select_for_update().filter(year=year).aggregate(Max("seq"))["seq__max"] or 0
        instance.year = year
        instance.seq = max_seq + 1

def render_html_to_pdf_bytes(html: str, base_url=None, extra_css_paths: list[str] | None = None) -> bytes:
    stylesheets = []
    css_path = finders.find('css/print.css')
    if css_path:
        stylesheets.append(CSS(filename=css_path))
    if extra_css_paths:
        for p in extra_css_paths:
            if p:
                stylesheets.append(CSS(filename=p))
    return HTML(string=html, base_url=base_url).write_pdf(stylesheets=stylesheets or None)
