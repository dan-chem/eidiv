# dienst/services.py
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from .models import Dienst

def assign_running_number(instance):
    now = timezone.now()
    if getattr(instance, "year", None) and getattr(instance, "seq", None):
        return
    with transaction.atomic():
        year = now.year
        max_seq = Dienst.objects.select_for_update().filter(year=year).aggregate(Max("seq"))["seq__max"] or 0
        instance.year = year
        instance.seq = max_seq + 1
