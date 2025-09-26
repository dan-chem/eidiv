# einsatz/views.py
from django.contrib import messages
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import JsonResponse
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from core.models import Einsatzstichwort

from .models import Einsatz
from .forms import (
    EinsatzForm, EinsatzPersonForm,
    LoeschwasserFormSet, EinsatzmittelFormSet,
    EinsatzFahrzeugFormSet, EinsatzAbrollFormSet, EinsatzAnhaengerFormSet, EinsatzOrtsfeuerwehrFormSet, ZusatzstelleFormSet,
    EinsatzTeilnahmeFormSet,
)
from .services import assign_running_number, render_html_to_pdf_bytes, send_mail_with_pdf

@login_required
def einsatz_neu(request):
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
        zs_fs = ZusatzstelleFormSet(request.POST, instance=e, prefix="zs")  # neu
        tn_fs = EinsatzTeilnahmeFormSet(request.POST, instance=e, prefix="tn")

        forms_valid = all([
            form.is_valid(), person_form.is_valid(),
            lw_fs.is_valid(), em_fs.is_valid(),
            vf_fs.is_valid(), ab_fs.is_valid(), an_fs.is_valid(), of_fs.is_valid(),
            zs_fs.is_valid(),  # neu
            tn_fs.is_valid(),
        ])

        if forms_valid:
            with transaction.atomic():
                e = form.save(commit=False)
                assign_running_number(e, type(e))
                e.full_clean()
                e.save()
                form.save_m2m()  # derzeit keine M2M ohne Through mehr im Form

                person = person_form.save(commit=False)
                person.einsatz = e
                person.full_clean()
                person.save()

                lw_fs.instance = e; lw_fs.save()
                em_fs.instance = e; em_fs.save()
                vf_fs.instance = e; vf_fs.save()
                ab_fs.instance = e; ab_fs.save()
                an_fs.instance = e; an_fs.save()
                of_fs.instance = e; of_fs.save()
                zs_fs.instance = e; zs_fs.save()  # neu
                tn_fs.instance = e; tn_fs.save()

            html = render_to_string("einsatz/pdf.html", {"obj": e})
            pdf_bytes = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
            subject = "Neue Einsatzliste eingegangen"
            body = "Automatische Nachricht: Eine neue Einsatzliste wurde erfasst."
            send_mail_with_pdf(subject, body, pdf_bytes, f"Einsatz_{e.nummer_formatiert}.pdf")
            messages.success(request, f"Einsatz {e.nummer_formatiert} gespeichert.")
            return redirect(reverse("einsatz_detail", args=[e.id]))
        else:
            return render(request, "einsatz/form.html", {
                "form": form, "person_form": person_form,
                "lw_fs": lw_fs, "em_fs": em_fs,
                "vf_fs": vf_fs, "ab_fs": ab_fs, "an_fs": an_fs, "of_fs": of_fs,
                "zs_fs": zs_fs,  # neu
                "tn_fs": tn_fs,
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
        zs_fs = ZusatzstelleFormSet(instance=e, prefix="zs")  # neu
        tn_fs = EinsatzTeilnahmeFormSet(instance=e, prefix="tn")

    return render(request, "einsatz/form.html", {
        "form": form, "person_form": person_form,
        "lw_fs": lw_fs, "em_fs": em_fs,
        "vf_fs": vf_fs, "ab_fs": ab_fs, "an_fs": an_fs, "of_fs": of_fs,
        "zs_fs": zs_fs,  # neu
        "tn_fs": tn_fs,
    })

@login_required
def einsatz_detail(request, pk: int):
    obj = get_object_or_404(Einsatz, pk=pk)
    return render(request, "einsatz/detail.html", {"obj": obj})

@login_required
def einsatz_pdf(request, pk: int):
    obj = get_object_or_404(Einsatz, pk=pk)
    html = render_to_string("einsatz/pdf.html", {"obj": obj})
    pdf_bytes = render_html_to_pdf_bytes(html)
    from django.http import HttpResponse
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
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_loeschwasser_row.html", {"form": form})

@login_required
def htmx_add_einsatzmittel(request):
    e = Einsatz()
    fs = EinsatzmittelFormSet(instance=e, prefix="em")
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_einsatzmittel_row.html", {"form": form})

@login_required
def htmx_add_fahrzeug(request):
    e = Einsatz()
    fs = EinsatzFahrzeugFormSet(instance=e, prefix="vf")
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_fahrzeug_row.html", {"form": form})

@login_required
def htmx_add_abroll(request):
    e = Einsatz()
    fs = EinsatzAbrollFormSet(instance=e, prefix="ab")
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_abroll_row.html", {"form": form})

@login_required
def htmx_add_anhaenger(request):
    e = Einsatz()
    fs = EinsatzAnhaengerFormSet(instance=e, prefix="an")
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_anhaenger_row.html", {"form": form})

@login_required
def htmx_add_ortsfeuerwehr(request):
    e = Einsatz()
    fs = EinsatzOrtsfeuerwehrFormSet(instance=e, prefix="of")
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_ortsfeuerwehr_row.html", {"form": form})

@login_required
def htmx_add_zusatzstelle(request):
    e = Einsatz()
    fs = ZusatzstelleFormSet(instance=e, prefix="zs")
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_zusatzstelle_row.html", {"form": form})

@login_required
def htmx_add_teilnahme(request):
    e = Einsatz()
    fs = EinsatzTeilnahmeFormSet(instance=e, prefix="tn")
    form = fs._construct_form(fs.total_form_count())
    return render(request, "einsatz/_teilnahme_row.html", {"form": form})
