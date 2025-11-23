from django.contrib import admin, messages
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.urls import path, reverse
from django.utils.html import format_html
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.templatetags.static import static
from core.utils.files import safe_filename

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

# PDF-Renderer aus der App
from .services import render_html_to_pdf_bytes
# Zentraler Mail-Service (alle Empfänger/BCC/Timeout etc.)
from core.services.mail import send_mail_with_pdf_to_active


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
    # Stunden werden in der Neuanlage nicht mehr erfasst; Admin-Inline zeigt daher nur Fahrzeug, km und erforderlich
    fields = ("fahrzeug", "kilometer", "erforderlich")
    autocomplete_fields = ("fahrzeug",)

class EinsatzAbrollInline(admin.TabularInline):
    model = EinsatzAbrollbehaelter
    extra = 0
    fields = ("abrollbehaelter", "erforderlich")
    autocomplete_fields = ("abrollbehaelter",)

class EinsatzAnhaengerInline(admin.TabularInline):
    model = EinsatzAnhaenger
    extra = 0
    # Stunden nicht in Neuanlage; entfernen aus Inline-Ansicht
    fields = ("anhaenger", "kilometer", "erforderlich")
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

    # Eigene Admin-URLs
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:pk>/pdf/", self.admin_site.admin_view(self.view_pdf), name="einsatz_einsatz_pdf"),
            path("<int:pk>/resend/", self.admin_site.admin_view(self.resend_mail), name="einsatz_einsatz_resend"),
        ]
        return custom + urls

    # PDF inline anzeigen
    def view_pdf(self, request, pk: int, *args, **kwargs):
        obj = get_object_or_404(Einsatz, pk=pk)
        html = render_to_string("einsatz/pdf.html", {"obj": obj})
        pdf = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
        resp = HttpResponse(pdf, content_type="application/pdf")
        safe_name = safe_filename(f"Einsatz_{obj.nummer_formatiert}.pdf")  # <-- safe
        resp["Content-Disposition"] = f'inline; filename="{safe_name}"'
        return resp

    # Mail erneut mit PDF-Anhang verschicken (zentraler Mail-Service)
    def resend_mail(self, request, pk: int, *args, **kwargs):
        obj = get_object_or_404(Einsatz, pk=pk)
        css_url = request.build_absolute_uri(static('css/print.css'))
        html = render_to_string("einsatz/pdf.html", {"obj": obj})
        pdf = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
        sent = send_mail_with_pdf_to_active(
            subject="Neue Einsatzliste eingegangen",
            body_text="Automatische Nachricht: Eine neue Einsatzliste wurde erfasst.",
            pdf_bytes=pdf,
            filename=f"Einsatz_{obj.nummer_formatiert}.pdf",
            fail_silently=False,  # im Admin Fehler anzeigen
        )
        messages.success(request, f"E-Mail für Einsatz {obj.nummer_formatiert} erneut versendet ({sent} Empfänger).")
        return HttpResponseRedirect(reverse("admin:einsatz_einsatz_change", args=[obj.pk]))

    # Bulk-Action: Mails erneut senden
    @admin.action(description="PDF per Mail erneut senden")
    def action_resend_mail(self, request, queryset):
        total_sent = 0
        for obj in queryset:
            html = render_to_string("einsatz/pdf.html", {"obj": obj})
            pdf = render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
            total_sent += send_mail_with_pdf_to_active(
                subject="Neue Einsatzliste eingegangen",
                body_text="Automatische Nachricht: Eine neue Einsatzliste wurde erfasst.",
                pdf_bytes=pdf,
                filename=f"Einsatz_{obj.nummer_formatiert}.pdf",
                fail_silently=False,
            )
        messages.success(request, f"E-Mails erneut versendet für {queryset.count()} Einsatz(e) (Summe Empfänger: {total_sent}).")

    actions = ["action_resend_mail"]
