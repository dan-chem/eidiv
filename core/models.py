# core/models.py
from django.db import models

class Mitglied(models.Model):
    name = models.CharField(max_length=80)
    vorname = models.CharField(max_length=80)
    agt = models.BooleanField(default=False, verbose_name="Atemschutzgeräteträger")
    hauptamtlich = models.BooleanField(default=False)
    kommandant = models.BooleanField(default=False)
    stv_kommandant = models.BooleanField(default=False)

    class Meta:
        ordering = ["name", "vorname"]

    def __str__(self):
        return f"{self.name}, {self.vorname}"

class Fahrzeug(models.Model):
    typ = models.CharField(max_length=80)
    funkrufname = models.CharField(max_length=80)
    kennzeichen = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ["funkrufname", "typ"]

    def __str__(self):
        return f"{self.funkrufname} ({self.typ})"

class Abrollbehaelter(models.Model):
    typ = models.CharField(max_length=80)

    def __str__(self):
        return self.typ

class Anhaenger(models.Model):
    typ = models.CharField(max_length=80)
    kennzeichen = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.typ}"

class Zusatzstelle(models.Model):
    typ = models.CharField(max_length=120)

    def __str__(self):
        return self.typ

class Einsatzmittel(models.Model):
    typ = models.CharField(max_length=120)

    def __str__(self):
        return self.typ

class MeldendeStelle(models.Model):
    name = models.CharField(max_length=120)

    def __str__(self):
        return self.name

class Brandumfang(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Brandausbreitung(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Brandgut(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Brandobjekt(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Loeschwasserentnahmestelle(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Schadensereignis(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class PersonenrettungTyp(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Sicherheitswache(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Fehlalarm(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Sonstige(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Ortsfeuerwehr(models.Model):
    typ = models.CharField(max_length=120)
    def __str__(self): return self.typ

class Einsatzstichwort(models.Model):
    KAT_BRAND = "brand"
    KAT_THL = "thl"
    KAT_SONST = "sonstig"
    KAT_ABC = "abc"
    KAT_INFO = "info"
    KATEGORIE_CHOICES = [
        (KAT_BRAND, "Brand"),
        (KAT_THL, "Technische Hilfeleistung"),
        (KAT_ABC, "ABC-Einsatz"),
        (KAT_INFO, "Infoeinsatz"),
        (KAT_SONST, "Sonstige"),
    ]
    code = models.CharField(max_length=40, blank=True)
    bezeichnung = models.CharField(max_length=120)
    aktiv = models.BooleanField(default=True)
    kategorie = models.CharField(max_length=16, choices=KATEGORIE_CHOICES, default=KAT_SONST)

    class Meta:
        ordering = ["bezeichnung"]

    def __str__(self):
        return f"{self.code + ' - ' if self.code else ''}{self.bezeichnung}"

class MailEmpfaenger(models.Model):
    email = models.EmailField(unique=True)
    aktiv = models.BooleanField(default=True)

    def __str__(self):
        return self.email
