# einsatz/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.template.loader import render_to_string
from django.contrib import messages

from .models import Einsatz
from .forms import EinsatzForm, EinsatzPersonForm, LoeschwasserFormSet, EinsatzmittelFormSet
from .services import assign_running_number, render_html_to_pdf_bytes, send_mail_with_pdf

def einsatz_neu(request):
    if request.method == "POST":
        einsatz = Einsatz()
        form = EinsatzForm(request.POST, instance=einsatz)
        person_form = EinsatzPersonForm(request.POST, instance=getattr(einsatz, "person", None))
        if form.is_valid():
            with transaction.atomic():
                einsatz = form.save(commit=False)
                assign_running_number(einsatz, Einsatz)
                einsatz.full_clean()
                einsatz.save()
                # OneToOne Person
                person_form.instance = getattr(einsatz, "person", None) or None
                if person_form.is_valid():
                    person_obj = person_form.save(commit=False)
                    person_obj.einsatz = einsatz
                    person_obj.save()
                # Formsets
                lw_formset = LoeschwasserFormSet(request.POST, instance=einsatz, prefix="lw")
                em_formset = EinsatzmittelFormSet(request.POST, instance=einsatz, prefix="em")
                if lw_formset.is_valid() and em_formset.is_valid():
                    lw_formset.save()
                    em_formset.save()
                else:
                    raise ValueError("Fehler in Löschwasser/Einsatzmittel")
            # PDF erstellen
            html = render_to_string("einsatz/pdf.html", {"obj": einsatz})
            pdf_bytes = render_html_to_pdf_bytes(html)
            # Mail
            subject = "Neue Einsatzliste eingegangen"
            body = "Automatische Nachricht: Eine neue Einsatzliste wurde erfasst."
            send_mail_with_pdf(subject, body, pdf_bytes, f"Einsatz_{einsatz.nummer_formatiert}.pdf")
            # Download als Response: hier pragmatisch Redirect auf Detail, wo Download-Link angeboten wird
            messages.success(request, f"Einsatz {einsatz.nummer_formatiert} gespeichert.")
            return redirect(reverse("einsatz_detail", args=[einsatz.id]))
    else:
        form = EinsatzForm()
        person_form = EinsatzPersonForm()
        lw_formset = LoeschwasserFormSet(prefix="lw", instance=Einsatz())
        em_formset = EinsatzmittelFormSet(prefix="em", instance=Einsatz())
    return render(request, "einsatz/form.html", {
        "form": form,
        "person_form": person_form,
        "lw_formset": lw_formset,
        "em_formset": em_formset,
    })

def einsatz_detail(request, pk):
    obj = get_object_or_404(Einsatz, pk=pk)
    return render(request, "einsatz/detail.html", {"obj": obj})

# HTMX: neue Zeile zu Formset hinzufügen (Client erhöht total_forms und holt ein Row-Fragment)
from django.forms import formset_factory
def htmx_add_loeschwasser(request):
    einsatz = Einsatz()  # ungebunden
    formset = LoeschwasserFormSet(prefix="lw", instance=einsatz)
    # künstlich eine extra-Form hinzufügen
    form = formset._construct_form(formset.total_form_count())
    return render(request, "einsatz/_loeschwasser_row.html", {"form": form})

def htmx_add_einsatzmittel(request):
    einsatz = Einsatz()
    formset = EinsatzmittelFormSet(prefix="em", instance=einsatz)
    form = formset._construct_form(formset.total_form_count())
    return render(request, "einsatz/_einsatzmittel_row.html", {"form": form})
