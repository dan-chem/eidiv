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

from weasyprint import HTML

from core.models import MailEmpfaenger
from .models import (
    Dienst,
    DienstFahrzeug,
    DienstAnhaenger,
    DienstTeilnahme,
)


# ---------- Helpers ----------

def assign_running_number(instance: Dienst):
    """
    Vergibt seq (001, 002, ...) pro Jahr transaktional.
    """
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


def render_html_to_pdf_bytes(html: str) -> bytes:
    return HTML(string=html, base_url="").write_pdf()


def send_mail_with_pdf(subject: str, body_text: str, pdf_bytes: bytes, filename: str) -> int:
    recipients = list(
        MailEmpfaenger.objects.filter(aktiv=True).values_list("email", flat=True)
    )
    if not recipients:
        return 0
    msg = EmailMessage(subject=subject, body=body_text, to=recipients)
    msg.attach(filename, pdf_bytes, "application/pdf")
    return msg.send(fail_silently=True)


# ---------- Forms / Formsets ----------

class DienstForm(forms.ModelForm):
    class Meta:
        model = Dienst
        fields = ["titel", "start_dt", "ende_dt", "beschreibung", "abrollbehaelter"]
        widgets = {
            "titel": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "start_dt": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "mt-1 w-full border rounded px-3 py-2"}),
            "ende_dt": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "mt-1 w-full border rounded px-3 py-2"}),
            "beschreibung": forms.Textarea(attrs={"class": "mt-1 w-full border rounded px-3 py-2", "rows": 4}),
            "abrollbehaelter": forms.CheckboxSelectMultiple(),  # Checkboxen statt Multi-Select
        }


DienstFahrzeugFormSet = inlineformset_factory(
    parent_model=Dienst,
    model=DienstFahrzeug,
    fields=["fahrzeug", "kilometer", "stunden"],
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
    """
    Erfassung eines neuen Dienstes inkl. Through-Tabellen per Inline-Formsets.
    - Vergabe der Nummer (001/JJJJ)
    - PDF-Erzeugung (WeasyPrint)
    - Versand per E-Mail an konfigurierte Empfänger
    """
    if request.method == "POST":
        d = Dienst()
        form = DienstForm(request.POST, instance=d)

        # Unbedingt erst an ein konkretes Dienst-Objekt binden (instance=d),
        # damit save() und spätere save_m2m() korrekt funktionieren.
        fv_formset = DienstFahrzeugFormSet(request.POST, instance=d, prefix="fv")
        an_formset = DienstAnhaengerFormSet(request.POST, instance=d, prefix="an")
        tn_formset = DienstTeilnahmeFormSet(request.POST, instance=d, prefix="tn")

        if form.is_valid() and fv_formset.is_valid() and an_formset.is_valid() and tn_formset.is_valid():
            with transaction.atomic():
                d = form.save(commit=False)
                assign_running_number(d)
                d.full_clean()  # prüft u. a. Start < Ende
                d.save()
                form.save_m2m()  # speichert abrollbehaelter (M2M ohne Through)

                fv_formset.instance = d
                an_formset.instance = d
                tn_formset.instance = d

                fv_formset.save()
                an_formset.save()
                tn_formset.save()

            # PDF erzeugen
            html = render_to_string("dienst/pdf.html", {"obj": d})
            pdf_bytes = render_html_to_pdf_bytes(html)

            # Mail versenden
            subject = "Neue Dienstliste eingegangen"
            body = "Automatische Nachricht: Eine neue Dienstliste wurde erfasst."
            send_mail_with_pdf(subject, body, pdf_bytes, f"Dienst_{d.nummer_formatiert}.pdf")

            messages.success(request, f"Dienst {d.nummer_formatiert} gespeichert.")
            return redirect(reverse("dienst_detail", args=[d.id]))
        else:
            # Fehlerhafte Formulare erneut anzeigen
            return render(
                request,
                "dienst/form.html",
                {
                    "form": form,
                    "fv_formset": fv_formset,
                    "an_formset": an_formset,
                    "tn_formset": tn_formset,
                },
                status=400,
            )
    else:
        d = Dienst()
        form = DienstForm(instance=d)
        fv_formset = DienstFahrzeugFormSet(instance=d, prefix="fv")
        an_formset = DienstAnhaengerFormSet(instance=d, prefix="an")
        tn_formset = DienstTeilnahmeFormSet(instance=d, prefix="tn")

    return render(
        request,
        "dienst/form.html",
        {
            "form": form,
            "fv_formset": fv_formset,
            "an_formset": an_formset,
            "tn_formset": tn_formset,
        },
    )


def dienst_detail(request, pk: int):
    obj = get_object_or_404(Dienst, pk=pk)
    return render(request, "dienst/detail.html", {"obj": obj})


def dienst_pdf(request, pk: int):
    """
    Liefert das PDF als Download für einen gespeicherten Dienst.
    """
    obj = get_object_or_404(Dienst, pk=pk)
    html = render_to_string("dienst/pdf.html", {"obj": obj})
    pdf_bytes = render_html_to_pdf_bytes(html)

    from django.http import HttpResponse
    resp = HttpResponse(pdf_bytes, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="Dienst_{obj.nummer_formatiert}.pdf"'
    return resp


# ---------- HTMX: Zeilen hinzufügen (optional) ----------

def htmx_add_fahrzeug(request):
    """
    Gibt eine zusätzliche Formularzeile für DienstFahrzeug zurück.
    Erwartet, dass das Template 'dienst/_fahrzeug_row.html' existiert.
    """
    d = Dienst()
    formset = DienstFahrzeugFormSet(instance=d, prefix="fv")
    form = formset._construct_form(formset.total_form_count())
    return render(request, "dienst/_fahrzeug_row.html", {"form": form})


def htmx_add_anhaenger(request):
    """
    Gibt eine zusätzliche Formularzeile für DienstAnhaenger zurück.
    Erwartet, dass das Template 'dienst/_anhaenger_row.html' existiert.
    """
    d = Dienst()
    formset = DienstAnhaengerFormSet(instance=d, prefix="an")
    form = formset._construct_form(formset.total_form_count())
    return render(request, "dienst/_anhaenger_row.html", {"form": form})


def htmx_add_teilnahme(request):
    """
    Gibt eine zusätzliche Formularzeile für DienstTeilnahme zurück.
    Erwartet, dass das Template 'dienst/_teilnahme_row.html' existiert.
    """
    d = Dienst()
    formset = DienstTeilnahmeFormSet(instance=d, prefix="tn")
    form = formset._construct_form(formset.total_form_count())
    return render(request, "dienst/_teilnahme_row.html", {"form": form})
