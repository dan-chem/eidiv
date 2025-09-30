# einsatz/views.py (Ausschnitt: Imports – optional EinsatzTeilnahmeFormSet entfernen)
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.conf import settings
from django.templatetags.static import static

from core.forms import TeilnahmeAlleMitgliederForm
from core.models import Mitglied, Einsatzstichwort
from core.services.mail import send_mail_with_pdf_to_active

from .models import Einsatz, EinsatzTeilnahme

from .forms import (
    EinsatzForm, EinsatzPersonForm,
    LoeschwasserFormSet, EinsatzmittelFormSet,
    EinsatzFahrzeugFormSet, EinsatzAbrollFormSet, EinsatzAnhaengerFormSet, EinsatzOrtsfeuerwehrFormSet, ZusatzstelleFormSet,
    # EinsatzTeilnahmeFormSet,  # <- NICHT MEHR VERWENDEN
)
from .services import assign_running_number, render_html_to_pdf_bytes

def _build_grouped_rows(forms, members):
    rows = []
    prev = None
    for f, m in zip(forms, members):
        initial = (m.name[:1] or "").upper()
        show_initial = initial != prev
        rows.append({"form": f, "m": m, "initial": initial, "show_initial": show_initial})
        prev = initial
    return rows

@login_required
def einsatz_neu(request):
    TeilnahmeFS = formset_factory(TeilnahmeAlleMitgliederForm, extra=0)

    if request.method == "POST":
        e = Einsatz()
        form = EinsatzForm(request.POST, instance=e)
        person_form = EinsatzPersonForm(request.POST, prefix="person")
        lw_fs = LoeschwasserFormSet(request.POST, instance=e, prefix="lw")
        em_fs = EinsatzmittelFormSet(request.POST, instance=e, prefix="em")
        vf_fs = EinsatzFahrzeugFormSet(request.POST, instance=e, prefix="vf")
        ab_fs = EinsatzAbrollFormSet(request.POST, instance=e, prefix="ab")
        an_fs = EinsatzAnhaengerFormSet(request.POST, instance=e, prefix="an")
        of_fs = EinsatzOrtsfeuerwehrFormSet(request.POST, instance=e, prefix="of")
        zs_fs = ZusatzstelleFormSet(request.POST, instance=e, prefix="zs")

        tn_formset = TeilnahmeFS(request.POST, prefix="tn")

        forms_valid = all([
            form.is_valid(), person_form.is_valid(),
            lw_fs.is_valid(), em_fs.is_valid(),
            vf_fs.is_valid(), ab_fs.is_valid(), an_fs.is_valid(), of_fs.is_valid(),
            zs_fs.is_valid(),
            tn_formset.is_valid(),
        ])

        if forms_valid:
            with transaction.atomic():
                e = form.save(commit=False)
                assign_running_number(e, type(e))
                e.full_clean(); e.save(); form.save_m2m()

                person = person_form.save(commit=False)
                person.einsatz = e
                person.full_clean(); person.save()

                lw_fs.instance = e; lw_fs.save()
                em_fs.instance = e; em_fs.save()
                vf_fs.instance = e; vf_fs.save()
                ab_fs.instance = e; ab_fs.save()
                an_fs.instance = e; an_fs.save()
                of_fs.instance = e; of_fs.save()
                zs_fs.instance = e; zs_fs.save()

                members = {m.id: m for m in Mitglied.objects.all()}
                existing = {t.mitglied_id: t for t in e.einsatzteilnahme_set.all()}
                for cd in tn_formset.cleaned_data:
                    mid = cd["mitglied_id"]
                    selected = bool(cd.get("selected"))
                    funk = cd.get("fahrzeug_funktion") or ""
                    agt_min = cd.get("agt_minuten")
                    is_agt = bool(members.get(mid) and members[mid].agt)

                    if selected:
                        obj = existing.get(mid) or EinsatzTeilnahme(einsatz=e, mitglied_id=mid)
                        obj.fahrzeug_funktion = funk
                        obj.agt_minuten = agt_min if is_agt and agt_min is not None else None
                        obj.full_clean(); obj.save()
                    else:
                        if mid in existing:
                            existing[mid].delete()

            css_url = request.build_absolute_uri(static('css/print.css'))
            html = render_to_string("einsatz/pdf.html", {"obj": e, "print_css_url": css_url})
            pdf_bytes = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
            try:
                send_mail_with_pdf_to_active(
                    subject="Neue Einsatzliste eingegangen",
                    body_text="Automatische Nachricht: Eine neue Einsatzliste wurde erfasst.",
                    pdf_bytes=pdf_bytes,
                    filename=f"Einsatz_{e.nummer_formatiert}.pdf",
                    fail_silently=False,  # Fehler explizit fangen
                )
            except Exception:
                import logging
                logging.getLogger(__name__).exception("Mailversand Einsatz %s fehlgeschlagen", e.nummer_formatiert)
                messages.warning(request, "Einsatz gespeichert, aber E-Mail-Versand fehlgeschlagen. Bitte Admin informieren.")
            return redirect(reverse("einsatz_detail", args=[e.id]))
        else:
            # Sortiert nach Nachname, Vorname; aktive oben, JF unten
            members_active = list(Mitglied.objects.filter(jugendfeuerwehr=False).order_by("name", "vorname"))
            members_jf = list(Mitglied.objects.filter(jugendfeuerwehr=True).order_by("name", "vorname"))

            # Formreihenfolge entspricht der Reihenfolge members_active + members_jf aus dem GET-Aufbau
            total_active = len(members_active)
            tn_rows_active = _build_grouped_rows(tn_formset.forms[:total_active], members_active)
            tn_rows_jf = _build_grouped_rows(tn_formset.forms[total_active:], members_jf)

            return render(request, "einsatz/form.html", {
                "form": form, "person_form": person_form,
                "lw_fs": lw_fs, "em_fs": em_fs,
                "vf_fs": vf_fs, "ab_fs": ab_fs, "an_fs": an_fs, "of_fs": of_fs,
                "zs_fs": zs_fs,
                "tn_formset": tn_formset,
                "tn_rows_active": tn_rows_active,
                "tn_rows_jf": tn_rows_jf,
            }, status=400)
    else:
        e = Einsatz()
        form = EinsatzForm(instance=e)
        person_form = EinsatzPersonForm(prefix="person")
        lw_fs = LoeschwasserFormSet(instance=e, prefix="lw")
        em_fs = EinsatzmittelFormSet(instance=e, prefix="em")
        vf_fs = EinsatzFahrzeugFormSet(instance=e, prefix="vf")
        ab_fs = EinsatzAbrollFormSet(instance=e, prefix="ab")
        an_fs = EinsatzAnhaengerFormSet(instance=e, prefix="an")
        of_fs = EinsatzOrtsfeuerwehrFormSet(instance=e, prefix="of")
        zs_fs = ZusatzstelleFormSet(instance=e, prefix="zs")

        members_active = list(Mitglied.objects.filter(jugendfeuerwehr=False).order_by("name", "vorname"))
        members_jf = list(Mitglied.objects.filter(jugendfeuerwehr=True).order_by("name", "vorname"))
        members = members_active + members_jf
        initial = [{
            "mitglied_id": m.id,
            "selected": False,
            "fahrzeug_funktion": "",
            "agt_minuten": None,
        } for m in members]
        tn_formset = TeilnahmeFS(prefix="tn", initial=initial)

        total_active = len(members_active)
        tn_rows_active = _build_grouped_rows(tn_formset.forms[:total_active], members_active)
        tn_rows_jf = _build_grouped_rows(tn_formset.forms[total_active:], members_jf)

    return render(request, "einsatz/form.html", {
        "form": form, "person_form": person_form,
        "lw_fs": lw_fs, "em_fs": em_fs,
        "vf_fs": vf_fs, "ab_fs": ab_fs, "an_fs": an_fs, "of_fs": of_fs,
        "zs_fs": zs_fs,
        "tn_formset": tn_formset,
        "tn_rows_active": tn_rows_active,
        "tn_rows_jf": tn_rows_jf,
    })


@login_required
def einsatz_detail(request, pk: int):
    obj = get_object_or_404(Einsatz, pk=pk)
    return render(request, "einsatz/detail.html", {"obj": obj})

@login_required
def einsatz_pdf(request, pk: int):
    obj = get_object_or_404(Einsatz, pk=pk)
    css_url = request.build_absolute_uri(static('css/print.css'))
    html = render_to_string("einsatz/pdf.html", {"obj": obj, "print_css_url": css_url})
    pdf_bytes = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="Einsatz_{obj.nummer_formatiert}.pdf"'
    return resp

@login_required
def einsatz_liste(request):
    q = request.GET.get("q", "").strip()
    year = request.GET.get("year", "").strip()

    qs = Einsatz.objects.select_related("stichwort").order_by("-year", "-seq")
    if year.isdigit():
        qs = qs.filter(year=int(year))
    if q:
        qs = qs.filter(
            Q(stichwort__bezeichnung__icontains=q) |
            Q(objektname__icontains=q) |
            Q(einsatzgemeinde__icontains=q) |
            Q(strasse_hausnr__icontains=q) |
            Q(plz_ort__icontains=q)
        )

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "einsatz/list.html", {"page_obj": page_obj, "q": q, "year": year})

@login_required
def stichwort_kategorie_api(request, pk: int):
    try:
        esw = Einsatzstichwort.objects.get(pk=pk)
        return JsonResponse({"kategorie": esw.kategorie})
    except Einsatzstichwort.DoesNotExist:
        return JsonResponse({"kategorie": "sonstig"})

@login_required
def stichwort_options(request):
    # akzeptiere sowohl ?kat=… als auch ?stichwort_kategorie=…
    kat = request.GET.get("kat") or request.GET.get("stichwort_kategorie")
    qs = Einsatzstichwort.objects.filter(aktiv=True)
    if kat:
        qs = qs.filter(kategorie=kat)
    # Reine Options-Liste zurückgeben
    html = ['<option value="">— bitte wählen —</option>']
    for sw in qs.order_by("bezeichnung"):
        html.append(f'<option value="{sw.pk}">{sw}</option>')
    return HttpResponse("\n".join(html), content_type="text/html")


# HTMX-Add: liefert eine zusätzliche Zeile je Formset
@login_required
def htmx_add_loeschwasser(request):
    e = Einsatz()
    fs = LoeschwasserFormSet(instance=e, prefix="lw")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "einsatz/_loeschwasser_row.html", {
        "form": form,
        "prefix": "lw",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_einsatzmittel(request):
    e = Einsatz()
    fs = EinsatzmittelFormSet(instance=e, prefix="em")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "einsatz/_einsatzmittel_row.html", {
        "form": form,
        "prefix": "em",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_fahrzeug(request):
    e = Einsatz()
    fs = EinsatzFahrzeugFormSet(instance=e, prefix="vf")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "einsatz/_fahrzeug_row.html", {
        "form": form,
        "prefix": "vf",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_abroll(request):
    e = Einsatz()
    fs = EinsatzAbrollFormSet(instance=e, prefix="ab")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "einsatz/_abroll_row.html", {
        "form": form,
        "prefix": "ab",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_anhaenger(request):
    e = Einsatz()
    fs = EinsatzAnhaengerFormSet(instance=e, prefix="an")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "einsatz/_anhaenger_row.html", {
        "form": form,
        "prefix": "an",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_ortsfeuerwehr(request):
    e = Einsatz()
    fs = EinsatzOrtsfeuerwehrFormSet(instance=e, prefix="of")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "einsatz/_ortsfeuerwehr_row.html", {
        "form": form,
        "prefix": "of",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_zusatzstelle(request):
    e = Einsatz()
    fs = ZusatzstelleFormSet(instance=e, prefix="zs")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "einsatz/_zusatzstelle_row.html", {
        "form": form,
        "prefix": "zs",
        "new_total": idx + 1,
    })
