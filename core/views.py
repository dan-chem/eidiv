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
    # Aktuelles Jahr und Zähler
    year = timezone.now().year
    einsatz_count = Einsatz.objects.filter(year=year).count()
    dienst_count = Dienst.objects.filter(year=year).count()

    # Jahres-Tabs für Startseite: verfügbare Jahre je Typ
    einsatz_years_qs = Einsatz.objects.order_by("-year").values_list("year", flat=True).distinct()
    einsatz_years = [y for y in einsatz_years_qs if y is not None]
    dienst_years_qs = Dienst.objects.order_by("-year").values_list("year", flat=True).distinct()
    dienst_years = [y for y in dienst_years_qs if y is not None]

    # Ggf. per GET-Parameter gefilterte Anzeige (e_year, d_year)
    e_year = request.GET.get("e_year")
    d_year = request.GET.get("d_year")

    recent_einsaetze_qs = Einsatz.objects.select_related("stichwort").order_by("-year", "-seq")
    recent_dienste_qs = Dienst.objects.order_by("-year", "-seq")
    if e_year and e_year.isdigit():
        recent_einsaetze_qs = recent_einsaetze_qs.filter(year=int(e_year))
    if d_year and d_year.isdigit():
        recent_dienste_qs = recent_dienste_qs.filter(year=int(d_year))

    recent_einsaetze = recent_einsaetze_qs[:5]
    recent_dienste = recent_dienste_qs[:5]

    return render(request, "index.html", {
        "year": year,
        "einsatz_count": einsatz_count,
        "dienst_count": dienst_count,
        "recent_einsaetze": recent_einsaetze,
        "recent_dienste": recent_dienste,
        "einsatz_years": einsatz_years,
        "dienst_years": dienst_years,
        "e_year": e_year,
        "d_year": d_year,
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
