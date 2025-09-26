# dienst/views.py
from django import forms
from django.contrib import messages
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Max
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone

from core.models import MailEmpfaenger
from .models import (
    Dienst,
    DienstFahrzeug,
    DienstAbrollbehaelter,
    DienstAnhaenger,
    DienstTeilnahme,
)

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

# ---------- Forms / Formsets ----------

class DienstForm(forms.ModelForm):
    class Meta:
        model = Dienst
        fields = ["titel", "start_dt", "ende_dt", "beschreibung"]  # abrollbehaelter hier entfernen
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
    extra=0,
    can_delete=True,
)

DienstAbrollFormSet = inlineformset_factory(
    parent_model=Dienst,
    model=DienstAbrollbehaelter,
    fields=["abrollbehaelter", "erforderlich"],
    extra=0,
    can_delete=True,
)

DienstAnhaengerFormSet = inlineformset_factory(
    parent_model=Dienst,
    model=DienstAnhaenger,
    fields=["anhaenger", "kilometer", "stunden"],
    extra=0,
    can_delete=True,
)

DienstTeilnahmeFormSet = inlineformset_factory(
    parent_model=Dienst,
    model=DienstTeilnahme,
    fields=["mitglied", "fahrzeug_funktion", "agt_minuten"],
    extra=0,
    can_delete=True,
)

# ---------- Views ----------

def dienst_neu(request):
    if request.method == "POST":
        d = Dienst()
        form = DienstForm(request.POST, instance=d)

        fv_formset = DienstFahrzeugFormSet(request.POST, instance=d, prefix="fv")
        ab_formset = DienstAbrollFormSet(request.POST, instance=d, prefix="ab")
        an_formset = DienstAnhaengerFormSet(request.POST, instance=d, prefix="an")
        tn_formset = DienstTeilnahmeFormSet(request.POST, instance=d, prefix="tn")

        if form.is_valid() and fv_formset.is_valid() and ab_formset.is_valid() and an_formset.is_valid() and tn_formset.is_valid():
            with transaction.atomic():
                d = form.save(commit=False)
                assign_running_number(d)
                d.full_clean()
                d.save()

                fv_formset.instance = d; fv_formset.save()
                ab_formset.instance = d; ab_formset.save()
                an_formset.instance = d; an_formset.save()
                tn_formset.instance = d; tn_formset.save()

            html = render_to_string("dienst/pdf.html", {"obj": d})
            pdf_bytes = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))

            subject = "Neue Dienstliste eingegangen"
            body = "Automatische Nachricht: Eine neue Dienstliste wurde erfasst."
            send_mail_with_pdf(subject, body, pdf_bytes, f"Dienst_{d.nummer_formatiert}.pdf")

            messages.success(request, f"Dienst {d.nummer_formatiert} gespeichert.")
            return redirect(reverse("dienst_detail", args=[d.id]))
        else:
            return render(request, "dienst/form.html", {
                "form": form,
                "fv_formset": fv_formset,
                "ab_formset": ab_formset,
                "an_formset": an_formset,
                "tn_formset": tn_formset,
            }, status=400)
    else:
        d = Dienst()
        form = DienstForm(instance=d)
        fv_formset = DienstFahrzeugFormSet(instance=d, prefix="fv")
        ab_formset = DienstAbrollFormSet(instance=d, prefix="ab")
        an_formset = DienstAnhaengerFormSet(instance=d, prefix="an")
        tn_formset = DienstTeilnahmeFormSet(instance=d, prefix="tn")

    return render(request, "dienst/form.html", {
        "form": form,
        "fv_formset": fv_formset,
        "ab_formset": ab_formset,
        "an_formset": an_formset,
        "tn_formset": tn_formset,
    })

def dienst_detail(request, pk: int):
    obj = get_object_or_404(Dienst, pk=pk)
    return render(request, "dienst/detail.html", {"obj": obj})

def dienst_pdf(request, pk: int):
    obj = get_object_or_404(Dienst, pk=pk)
    html = render_to_string("dienst/pdf.html", {"obj": obj})
    pdf_bytes = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
    from django.http import HttpResponse
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="Dienst_{obj.nummer_formatiert}.pdf"'
    return resp

# ---------- HTMX Add-Row ----------

def htmx_add_fahrzeug(request):
    d = Dienst()
    formset = DienstFahrzeugFormSet(instance=d, prefix="fv")
    form = formset._construct_form(formset.total_form_count())
    return render(request, "dienst/_fahrzeug_row.html", {"form": form})

def htmx_add_abroll(request):
    d = Dienst()
    formset = DienstAbrollFormSet(instance=d, prefix="ab")
    form = formset._construct_form(formset.total_form_count())
    return render(request, "dienst/_abroll_row.html", {"form": form})

def htmx_add_anhaenger(request):
    d = Dienst()
    formset = DienstAnhaengerFormSet(instance=d, prefix="an")
    form = formset._construct_form(formset.total_form_count())
    return render(request, "dienst/_anhaenger_row.html", {"form": form})

def htmx_add_teilnahme(request):
    d = Dienst()
    formset = DienstTeilnahmeFormSet(instance=d, prefix="tn")
    form = formset._construct_form(formset.total_form_count())
    return render(request, "dienst/_teilnahme_row.html", {"form": form})
