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

from weasyprint import HTML  # für PDF

from core.services.mail import send_mail_with_pdf_to_active
from core.utils.files import safe_filename

from .models import (
    Dienst,
    DienstFahrzeug,
    DienstAbrollbehaelter,
    DienstAnhaenger,
    DienstTeilnahme,
)

# Inlines
class DienstFahrzeugInline(admin.TabularInline):
    model = DienstFahrzeug
    extra = 0
    fields = ("fahrzeug", "kilometer", "stunden")
    # optional, wenn du viele Fahrzeuge hast: Autocomplete
    autocomplete_fields = ("fahrzeug",)

class DienstAbrollInline(admin.TabularInline):
    model = DienstAbrollbehaelter
    extra = 0
    fields = ("abrollbehaelter", "erforderlich")
    autocomplete_fields = ("abrollbehaelter",)

class DienstAnhaengerInline(admin.TabularInline):
    model = DienstAnhaenger
    extra = 0
    fields = ("anhaenger", "kilometer", "stunden")
    autocomplete_fields = ("anhaenger",)

class DienstTeilnahmeInline(admin.TabularInline):
    model = DienstTeilnahme
    extra = 0
    fields = ("mitglied", "fahrzeug_funktion", "agt_minuten")
    autocomplete_fields = ("mitglied",)

def _render_html_to_pdf_bytes(html: str, base_url=None) -> bytes:
    return HTML(string=html, base_url=base_url).write_pdf()

@admin.register(Dienst)
class DienstAdmin(admin.ModelAdmin):
    date_hierarchy = "start_dt"
    list_display = ("nummer_formatiert", "titel", "start_dt", "ende_dt", "obj_actions")
    search_fields = ("titel",)
    list_filter = ("year",)
    readonly_fields = ("year", "seq", "nummer_formatiert", "dauer_stunden")

    fieldsets = (
        ("Allgemein", {"fields": ("titel", "start_dt", "ende_dt", "beschreibung")}),
        ("Nummer/Meta", {
            "fields": ("year", "seq", "nummer_formatiert", "dauer_stunden"),
            "classes": ("collapse",),
        }),
    )

    inlines = [DienstFahrzeugInline, DienstAbrollInline, DienstAnhaengerInline, DienstTeilnahmeInline]

    # Objekt-Tools Spalte
    def obj_actions(self, obj):
        return format_html(
            '<a class="button" href="{}" target="_blank">PDF</a>&nbsp;'
            '<a class="button" href="{}">Mail erneut</a>',
            reverse('admin:dienst_dienst_pdf', args=[obj.pk]),
            reverse('admin:dienst_dienst_resend', args=[obj.pk]),
        )
    obj_actions.short_description = "Aktionen"

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("<int:pk>/pdf/", self.admin_site.admin_view(self.view_pdf), name="dienst_dienst_pdf"),
            path("<int:pk>/resend/", self.admin_site.admin_view(self.resend_mail), name="dienst_dienst_resend"),
        ]
        return custom + urls

    def view_pdf(self, request, pk: int, *args, **kwargs):
        obj = get_object_or_404(Dienst, pk=pk)
        html = render_to_string("dienst/pdf.html", {"obj": obj})
        pdf = _render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
        resp = HttpResponse(pdf, content_type="application/pdf")
        safe_name = safe_filename(f"Dienst_{obj.nummer_formatiert}.pdf")  # <-- safe
        resp["Content-Disposition"] = f'inline; filename="{safe_name}"'
        return resp

    def resend_mail(self, request, pk: int, *args, **kwargs):
        obj = get_object_or_404(Dienst, pk=pk)
        css_url = request.build_absolute_uri(static('css/print.css'))
        html = render_to_string("dienst/pdf.html", {"obj": obj, "print_css_url": css_url})
        pdf = _render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
        sent = send_mail_with_pdf_to_active(
            subject="Neue Dienstliste eingegangen",
            body_text="Automatische Nachricht: Eine neue Dienstliste wurde erfasst.",
            pdf_bytes=pdf,
            filename=f"Dienst_{obj.nummer_formatiert}.pdf",
            fail_silently=False,  # im Admin Fehler anzeigen
        )
        messages.success(request, f"E-Mail für Dienst {obj.nummer_formatiert} erneut versendet ({sent} Empfänger).")
        return HttpResponseRedirect(reverse("admin:dienst_dienst_change", args=[obj.pk]))

    # Bulk-Action: Mails erneut senden
    @admin.action(description="PDF per Mail erneut senden")
    def action_resend_mail(self, request, queryset):
        total_sent = 0
        for obj in queryset:
            html = render_to_string("dienst/pdf.html", {"obj": obj})
            pdf = _render_html_to_pdf_bytes(html, base_url=request.build_absolute_uri("/"))
            total_sent += send_mail_with_pdf_to_active(
                subject="Neue Dienstliste eingegangen",
                body_text="Automatische Nachricht: Eine neue Dienstliste wurde erfasst.",
                pdf_bytes=pdf,
                filename=f"Dienst_{obj.nummer_formatiert}.pdf",
                fail_silently=False,
            )
        messages.success(request, f"E-Mails erneut versendet für {queryset.count()} Dienst(e) (Summe Empfänger: {total_sent}).")

    actions = ["action_resend_mail"]
