# core/admin.py
from django.contrib import admin
from .models import (
    Mitglied, Fahrzeug, Abrollbehaelter, Anhaenger, Zusatzstelle, Einsatzmittel,
    MeldendeStelle, Brandumfang, Brandausbreitung, Brandgut, Brandobjekt,
    Loeschwasserentnahmestelle, Schadensereignis, PersonenrettungTyp,
    Sicherheitswache, Fehlalarm, Sonstige, Ortsfeuerwehr, Einsatzstichwort, MailEmpfaenger
)

# WICHTIG: Keine pauschale for-Schleife mehr – sonst doppelte Registrierung!

@admin.register(Mitglied)
class MitgliedAdmin(admin.ModelAdmin):
    search_fields = ("name", "vorname")
    list_display = ("name", "vorname", "agt", "hauptamtlich", "jugendfeuerwehr")
    list_filter = ("agt", "hauptamtlich", "jugendfeuerwehr")

@admin.register(Fahrzeug)
class FahrzeugAdmin(admin.ModelAdmin):
    search_fields = ("typ", "funkrufname", "kennzeichen")
    list_display = ("typ", "funkrufname", "kennzeichen")

@admin.register(Abrollbehaelter)
class AbrollbehaelterAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Anhaenger)
class AnhaengerAdmin(admin.ModelAdmin):
    search_fields = ("typ", "kennzeichen")
    list_display = ("typ", "kennzeichen")

@admin.register(Zusatzstelle)
class ZusatzstelleAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Einsatzmittel)
class EinsatzmittelAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(MeldendeStelle)
class MeldendeStelleAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    list_display = ("name",)

@admin.register(Brandumfang)
class BrandumfangAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Brandausbreitung)
class BrandausbreitungAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Brandgut)
class BrandgutAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Brandobjekt)
class BrandobjektAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Loeschwasserentnahmestelle)
class LoeschwasserentnahmestelleAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Schadensereignis)
class SchadensereignisAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(PersonenrettungTyp)
class PersonenrettungTypAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Sicherheitswache)
class SicherheitswacheAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Fehlalarm)
class FehlalarmAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Sonstige)
class SonstigeAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Ortsfeuerwehr)
class OrtsfeuerwehrAdmin(admin.ModelAdmin):
    search_fields = ("typ",)
    list_display = ("typ",)

@admin.register(Einsatzstichwort)
class EinsatzstichwortAdmin(admin.ModelAdmin):
    list_display = ("code", "bezeichnung", "kategorie", "aktiv")
    list_filter = ("kategorie", "aktiv")
    search_fields = ("code", "bezeichnung")

@admin.register(MailEmpfaenger)
class MailEmpfaengerAdmin(admin.ModelAdmin):
    list_display = ("email", "aktiv")
    search_fields = ("email",)
