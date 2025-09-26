# einsatz/admin.py
from django.contrib import admin
from .models import (Einsatz, EinsatzPerson, EinsatzLoeschwasser, EinsatzFahrzeug, EinsatzAbrollbehaelter,
                     EinsatzAnhaenger, EinsatzOrtsfeuerwehr, EinsatzEinsatzmittel, EinsatzTeilnahme)

class EinsatzLoeschwasserInline(admin.TabularInline):
    model = EinsatzLoeschwasser
    extra = 0

class EinsatzPersonInline(admin.StackedInline):
    model = EinsatzPerson
    extra = 0
    max_num = 1

@admin.register(Einsatz)
class EinsatzAdmin(admin.ModelAdmin):
    list_display = ("nummer_formatiert", "stichwort", "start_dt", "ende_dt")
    inlines = [EinsatzPersonInline, EinsatzLoeschwasserInline]
    search_fields = ("year", "seq", "stichwort__bezeichnung")
