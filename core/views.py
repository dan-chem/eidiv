# core/views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Mitglied
from django.contrib.auth.decorators import login_required
from django.utils import timezone

@login_required
def index(request):
    from einsatz.models import Einsatz
    from dienst.models import Dienst

    year = timezone.now().year
    einsatz_count = Einsatz.objects.filter(year=year).count()
    dienst_count = Dienst.objects.filter(year=year).count()

    recent_einsaetze = Einsatz.objects.select_related("stichwort").order_by("-year", "-seq")[:5]
    recent_dienste = Dienst.objects.order_by("-year", "-seq")[:5]

    return render(request, "index.html", {
        "year": year,
        "einsatz_count": einsatz_count,
        "dienst_count": dienst_count,
        "recent_einsaetze": recent_einsaetze,
        "recent_dienste": recent_dienste,
    })

def api_mitglied_agt(request, pk: int):
    """
    Liefert {"agt": true/false} für das Mitglied mit PK.
    Wird genutzt, um das Feld 'AGT (Min)' dynamisch zu aktivieren/deaktivieren.
    """
    try:
        m = Mitglied.objects.get(pk=pk)
        return JsonResponse({"agt": bool(m.agt)})
    except Mitglied.DoesNotExist:
        return JsonResponse({"agt": False})
