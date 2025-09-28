# dienst/views.py
from django import forms
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Max
from django.forms import inlineformset_factory, NumberInput, Select, TextInput, CheckboxInput
from django.forms import formset_factory  # neu
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from core.models import MailEmpfaenger
from core.models import Mitglied                     # neu
from core.forms import TeilnahmeAlleMitgliederForm   # neu

from .models import (
    Dienst,
    DienstFahrzeug,
    DienstAbrollbehaelter,
    DienstAnhaenger,
    DienstTeilnahme,
)

common = {"class": "w-full border rounded px-2 py-1"}

# ---------- Helpers ----------

def assign_running_number(instance: Dienst):
    if getattr(instance, "year", None) and getattr(instance, "seq", None):
        return
    now = timezone.now()
    with transaction.atomic():
        year = now.year
        max_seq = (
            Dienst.objects.select_for_update()
            .filter(year=year)
            .aggregate(Max("seq"))["seq__max"]
            or 0
        )
        instance.year = year
        instance.seq = max_seq + 1

def render_html_to_pdf_bytes(html: str, base_url=None) -> bytes:
    from weasyprint import HTML
    return HTML(string=html, base_url=base_url).write_pdf()

def send_mail_with_pdf(subject: str, body_text: str, pdf_bytes: bytes, filename: str) -> int:
    recipients = list(MailEmpfaenger.objects.filter(aktiv=True).values_list("email", flat=True))
    if not recipients:
        return 0
    msg = EmailMessage(subject=subject, body=body_text, to=recipients)
    msg.attach(filename, pdf_bytes, "application/pdf")
    return msg.send(fail_silently=True)

def _build_grouped_rows(forms, members):
    rows = []
    prev = None
    for f, m in zip(forms, members):
        initial = (m.name[:1] or "").upper()
        show_initial = initial != prev
        rows.append({"form": f, "m": m, "initial": initial, "show_initial": show_initial})
        prev = initial
    return rows

# ---------- Forms / Formsets ----------

class DienstForm(forms.ModelForm):
    class Meta:
        model = Dienst
        fields = ["titel", "start_dt", "ende_dt", "beschreibung"]
        widgets = {
            "titel": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "start_dt": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "mt-1 w-full border rounded px-3 py-2"}),
            "ende_dt": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "mt-1 w-full border rounded px-3 py-2"}),
            "beschreibung": forms.Textarea(attrs={"class": "mt-1 w-full border rounded px-3 py-2", "rows": 4}),
        }

DienstFahrzeugFormSet = inlineformset_factory(
    parent_model=Dienst,
    model=DienstFahrzeug,
    fields=["fahrzeug", "kilometer", "stunden"],
    widgets={
        "fahrzeug": Select(attrs=common),
        "kilometer": NumberInput(attrs={**common, "min": 0}),
        "stunden": NumberInput(attrs={**common, "min": 0, "step": "0.01"}),
    },
    extra=0,
    can_delete=True,
)

DienstAbrollFormSet = inlineformset_factory(
    parent_model=Dienst,
    model=DienstAbrollbehaelter,
    fields=["abrollbehaelter", "erforderlich"],
    widgets={
        "abrollbehaelter": Select(attrs=common),
        "erforderlich": CheckboxInput(),
    },
    extra=0,
    can_delete=True,
)

DienstAnhaengerFormSet = inlineformset_factory(
    parent_model=Dienst,
    model=DienstAnhaenger,
    fields=["anhaenger", "kilometer", "stunden"],
    widgets={
        "anhaenger": Select(attrs=common),
        "kilometer": NumberInput(attrs={**common, "min": 0}),
        "stunden": NumberInput(attrs={**common, "min": 0, "step": "0.01"}),
    },
    extra=0,
    can_delete=True,
)

# Hinweis: DienstTeilnahmeFormSet wird nicht mehr verwendet (Checkboxliste über alle Mitglieder)
# DienstTeilnahmeFormSet = inlineformset_factory(...)

# ---------- Views ----------

@login_required
def dienst_neu(request):
    TeilnahmeFS = formset_factory(TeilnahmeAlleMitgliederForm, extra=0)

    if request.method == "POST":
        d = Dienst()
        form = DienstForm(request.POST, instance=d)
        fv_formset = DienstFahrzeugFormSet(request.POST, instance=d, prefix="fv")
        ab_formset = DienstAbrollFormSet(request.POST, instance=d, prefix="ab")
        an_formset = DienstAnhaengerFormSet(request.POST, instance=d, prefix="an")
        tn_formset = TeilnahmeFS(request.POST, prefix="tn")

        if form.is_valid() and fv_formset.is_valid() and ab_formset.is_valid() and an_formset.is_valid() and tn_formset.is_valid():
            with transaction.atomic():
                d = form.save(commit=False)
                assign_running_number(d); d.full_clean(); d.save()

                fv_formset.instance = d; fv_formset.save()
                ab_formset.instance = d; ab_formset.save()
                an_formset.instance = d; an_formset.save()

                members = {m.id: m for m in Mitglied.objects.all()}
                existing = {t.mitglied_id: t for t in d.dienstteilnahme_set.all()}
                for cd in tn_formset.cleaned_data:
                    mid = cd["mitglied_id"]
                    selected = bool(cd.get("selected"))
                    funk = cd.get("fahrzeug_funktion") or ""
                    agt_min = cd.get("agt_minuten")
                    is_agt = bool(members.get(mid) and members[mid].agt)

                    if selected:
                        obj = existing.get(mid) or DienstTeilnahme(dienst=d, mitglied_id=mid)
                        obj.fahrzeug_funktion = funk
                        obj.agt_minuten = agt_min if is_agt and agt_min is not None else None
                        obj.full_clean(); obj.save()
                    else:
                        if mid in existing:
                            existing[mid].delete()

            html = render_to_string("dienst/pdf.html", {"obj": d})
            pdf_bytes = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
            send_mail_with_pdf("Neue Dienstliste eingegangen", "Automatische Nachricht: Eine neue Dienstliste wurde erfasst.", pdf_bytes, f"Dienst_{d.nummer_formatiert}.pdf")
            messages.success(request, f"Dienst {d.nummer_formatiert} gespeichert.")
            return redirect(reverse("dienst_detail", args=[d.id]))
        else:
            members_active = list(Mitglied.objects.filter(jugendfeuerwehr=False).order_by("name", "vorname"))
            members_jf = list(Mitglied.objects.filter(jugendfeuerwehr=True).order_by("name", "vorname"))
            total_active = len(members_active)
            tn_rows_active = _build_grouped_rows(tn_formset.forms[:total_active], members_active)
            tn_rows_jf = _build_grouped_rows(tn_formset.forms[total_active:], members_jf)
            return render(request, "dienst/form.html", {
                "form": form,
                "fv_formset": fv_formset, "ab_formset": ab_formset, "an_formset": an_formset,
                "tn_formset": tn_formset,
                "tn_rows_active": tn_rows_active,
                "tn_rows_jf": tn_rows_jf,
            }, status=400)
    else:
        d = Dienst()
        form = DienstForm(instance=d)
        fv_formset = DienstFahrzeugFormSet(instance=d, prefix="fv")
        ab_formset = DienstAbrollFormSet(instance=d, prefix="ab")
        an_formset = DienstAnhaengerFormSet(instance=d, prefix="an")

        members_active = list(Mitglied.objects.filter(jugendfeuerwehr=False).order_by("name", "vorname"))
        members_jf = list(Mitglied.objects.filter(jugendfeuerwehr=True).order_by("name", "vorname"))
        members = members_active + members_jf
        initial = [{
            "mitglied_id": m.id, "selected": False, "fahrzeug_funktion": "", "agt_minuten": None
        } for m in members]
        tn_formset = TeilnahmeFS(prefix="tn", initial=initial)

        total_active = len(members_active)
        tn_rows_active = _build_grouped_rows(tn_formset.forms[:total_active], members_active)
        tn_rows_jf = _build_grouped_rows(tn_formset.forms[total_active:], members_jf)

    return render(request, "dienst/form.html", {
        "form": form,
        "fv_formset": fv_formset, "ab_formset": ab_formset, "an_formset": an_formset,
        "tn_formset": tn_formset,
        "tn_rows_active": tn_rows_active,
        "tn_rows_jf": tn_rows_jf,
    })

@login_required
def dienst_detail(request, pk: int):
    obj = get_object_or_404(Dienst, pk=pk)
    return render(request, "dienst/detail.html", {"obj": obj})

@login_required
def dienst_pdf(request, pk: int):
    obj = get_object_or_404(Dienst, pk=pk)
    html = render_to_string("dienst/pdf.html", {"obj": obj})
    pdf_bytes = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
    from django.http import HttpResponse
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="Dienst_{obj.nummer_formatiert}.pdf"'
    return resp

@login_required
def dienst_liste(request):
    q = request.GET.get("q", "").strip()
    year = request.GET.get("year", "").strip()

    qs = Dienst.objects.order_by("-year", "-seq")
    if year.isdigit():
        qs = qs.filter(year=int(year))
    if q:
        qs = qs.filter(Q(titel__icontains=q))

    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "dienst/list.html", {"page_obj": page_obj, "q": q, "year": year})

# ---------- HTMX Add-Row ----------

@login_required
def htmx_add_fahrzeug(request):
    d = Dienst()
    fs = DienstFahrzeugFormSet(instance=d, prefix="fv")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "dienst/_fahrzeug_row.html", {
        "form": form,
        "prefix": "fv",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_abroll(request):
    d = Dienst()
    fs = DienstAbrollFormSet(instance=d, prefix="ab")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "dienst/_abroll_row.html", {
        "form": form,
        "prefix": "ab",
        "new_total": idx + 1,
    })

@login_required
def htmx_add_anhaenger(request):
    d = Dienst()
    fs = DienstAnhaengerFormSet(instance=d, prefix="an")
    idx = fs.total_form_count()
    form = fs._construct_form(idx)
    return render(request, "dienst/_anhaenger_row.html", {
        "form": form,
        "prefix": "an",
        "new_total": idx + 1,
    })
