# einsatz/admin.py
from django.contrib import admin
from .models import (Einsatz, EinsatzPerson, EinsatzLoeschwasser, EinsatzFahrzeug, EinsatzAbrollbehaelter,
                     EinsatzAnhaenger, EinsatzOrtsfeuerwehr, EinsatzZusatzstelle, EinsatzEinsatzmittel, EinsatzTeilnahme)

class EinsatzLoeschwasserInline(admin.TabularInline):
    model = EinsatzLoeschwasser
    extra = 0

class EinsatzPersonInline(admin.StackedInline):
    model = EinsatzPerson
    extra = 0
    max_num = 1

class EinsatzZusatzstelleInline(admin.TabularInline):
    model = EinsatzZusatzstelle
    extra = 0

@admin.register(Einsatz)
class EinsatzAdmin(admin.ModelAdmin):
    list_display = ("nummer_formatiert", "stichwort", "start_dt", "ende_dt")
    inlines = [EinsatzPersonInline, EinsatzLoeschwasserInline, EinsatzZusatzstelleInline]
    search_fields = ("year", "seq", "stichwort__bezeichnung")
