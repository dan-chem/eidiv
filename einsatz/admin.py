from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string

from .models import (
    Einsatz,
    EinsatzPerson,
    EinsatzLoeschwasser,
    EinsatzEinsatzmittel,
    EinsatzFahrzeug,
    EinsatzAbrollbehaelter,
    EinsatzAnhaenger,
    EinsatzOrtsfeuerwehr,
    EinsatzZusatzstelle,
    EinsatzTeilnahme,
)

# PDF/Mail-Helfer aus deinem Service wiederverwenden
from .services import render_html_to_pdf_bytes, send_mail_with_pdf

# Inlines
class EinsatzPersonInline(admin.StackedInline):
    model = EinsatzPerson
    extra = 0
    fields = (
        "typ",
        "name_vorname",
        "strasse_hausnr",
        "plz_ort",
        "telefon",
        "kfz_kennz",
        "kostenbefreit",
        "begruendung",
    )

class EinsatzLoeschwasserInline(admin.TabularInline):
    model = EinsatzLoeschwasser
    extra = 0
    fields = ("entnahmestelle", "menge")
    autocomplete_fields = ("entnahmestelle",)

class EinsatzEinsatzmittelInline(admin.TabularInline):
    model = EinsatzEinsatzmittel
    extra = 0
    fields = ("einsatzmittel", "anzahl")
    autocomplete_fields = ("einsatzmittel",)

class EinsatzFahrzeugInline(admin.TabularInline):
    model = EinsatzFahrzeug
    extra = 0
    fields = ("fahrzeug", "kilometer", "stunden", "erforderlich")
    autocomplete_fields = ("fahrzeug",)

class EinsatzAbrollInline(admin.TabularInline):
    model = EinsatzAbrollbehaelter
    extra = 0
    fields = ("abrollbehaelter", "erforderlich")
    autocomplete_fields = ("abrollbehaelter",)

class EinsatzAnhaengerInline(admin.TabularInline):
    model = EinsatzAnhaenger
    extra = 0
    fields = ("anhaenger", "kilometer", "stunden", "erforderlich")
    autocomplete_fields = ("anhaenger",)

class EinsatzOrtsfeuerwehrInline(admin.TabularInline):
    model = EinsatzOrtsfeuerwehr
    extra = 0
    fields = ("ortsfeuerwehr", "erforderlich")
    autocomplete_fields = ("ortsfeuerwehr",)

class EinsatzZusatzstelleInline(admin.TabularInline):
    model = EinsatzZusatzstelle
    extra = 0
    fields = ("zusatzstelle",)
    autocomplete_fields = ("zusatzstelle",)

class EinsatzTeilnahmeInline(admin.TabularInline):
    model = EinsatzTeilnahme
    extra = 0
    fields = ("mitglied", "fahrzeug_funktion", "agt_minuten")
    autocomplete_fields = ("mitglied",)

@admin.register(Einsatz)
class EinsatzAdmin(admin.ModelAdmin):
    date_hierarchy = "start_dt"
    list_display = ("nummer_formatiert", "stichwort", "start_dt", "ende_dt", "einsatzgemeinde", "obj_actions")
    list_filter = ("year", "stichwort__kategorie")
    search_fields = (
        "objektname",
        "strasse_hausnr",
        "plz_ort",
        "einsatzgemeinde",
        "landkreis",
        "einsatzmassnahmen",
        "stichwort__bezeichnung",
        "stichwort__code",
    )
    readonly_fields = ("year", "seq", "nummer_formatiert", "dauer_stunden")
    autocomplete_fields = ("stichwort", "einsatzleiter", "meldende_stelle")

    fieldsets = (
        ("Allgemeine Einsatzdaten", {
            "fields": (
                "stichwort",
                "start_dt", "ende_dt",
                "einsatzleiter", "einsatzleiter_text",
                "meldende_stelle",
            ),
        }),
        ("Einsatzort", {
            "fields": ("objektname", "strasse_hausnr", "plz_ort", "einsatzgemeinde", "landkreis"),
        }),
        ("Angaben zum Brand", {
            "fields": ("brandumfang", "brandausbreitung", "brandgut", "brandobjekt"),
            "classes": ("collapse",),
        }),
        ("Technische Hilfeleistung", {
            "fields": ("schadensereignis", "personenrettung_typ", "personenrettung_anzahl", "sicherheitswache", "fehlalarm", "sonstige"),
            "classes": ("collapse",),
        }),
        ("Maßnahmen/Material", {"fields": ("einsatzmassnahmen",)}),
        ("Nummer/Meta", {
            "fields": ("year", "seq", "nummer_formatiert", "dauer_stunden"),
            "classes": ("collapse",),
        }),
    )

    inlines = [
        EinsatzPersonInline,
        EinsatzLoeschwasserInline,
        EinsatzEinsatzmittelInline,
        EinsatzFahrzeugInline,
        EinsatzAbrollInline,
        EinsatzAnhaengerInline,
        EinsatzOrtsfeuerwehrInline,
        EinsatzZusatzstelleInline,
        EinsatzTeilnahmeInline,
    ]

    # Objekt-Tools Spalte
    def obj_actions(self, obj):
        return format_html(
            '<a class="button" href="{}" target="_blank">PDF</a>&nbsp;'
            '<a class="button" href="{}">Mail erneut</a>',
            reverse('admin:einsatz_einsatz_pdf', args=[obj.pk]),
            reverse('admin:einsatz_einsatz_resend', args=[obj.pk]),
        )
    obj_actions.short_description = "Aktionen"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:pk>/pdf/", self.admin_site.admin_view(self.view_pdf), name="einsatz_einsatz_pdf"),
            path("<int:pk>/resend/", self.admin_site.admin_view(self.resend_mail), name="einsatz_einsatz_resend"),
        ]
        return custom + urls

    def view_pdf(self, request, pk: int, *args, **kwargs):
        obj = get_object_or_404(Einsatz, pk=pk)
        html = render_to_string("einsatz/pdf.html", {"obj": obj})
        pdf = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
        resp = HttpResponse(pdf, content_type="application/pdf")
        resp["Content-Disposition"] = f'inline; filename="Einsatz_{obj.nummer_formatiert}.pdf"'
        return resp

    def resend_mail(self, request, pk: int, *args, **kwargs):
        obj = get_object_or_404(Einsatz, pk=pk)
        html = render_to_string("einsatz/pdf.html", {"obj": obj})
        pdf = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
        sent = send_mail_with_pdf(
            "Neue Einsatzliste eingegangen",
            "Automatische Nachricht: Eine neue Einsatzliste wurde erfasst.",
            pdf,
            f"Einsatz_{obj.nummer_formatiert}.pdf",
        )
        messages.success(request, f"E-Mail für Einsatz {obj.nummer_formatiert} erneut versendet ({sent} Empfänger).")
        return HttpResponseRedirect(reverse("admin:einsatz_einsatz_change", args=[obj.pk]))