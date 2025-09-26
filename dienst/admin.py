# dienst/admin.py
from django.contrib import admin
from .models import Dienst, DienstFahrzeug, DienstAnhaenger, DienstTeilnahme

@admin.register(Dienst)
class DienstAdmin(admin.ModelAdmin):
    list_display = ("nummer_formatiert", "titel", "start_dt", "ende_dt")
    search_fields = ("year", "seq", "titel")
