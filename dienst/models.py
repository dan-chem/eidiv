# dienst/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Sum
from core.models import Mitglied, Fahrzeug, Abrollbehaelter, Anhaenger

class Dienst(models.Model):
    year = models.PositiveIntegerField(editable=False)
    seq = models.PositiveIntegerField(editable=False)
    titel = models.CharField(max_length=160)
    start_dt = models.DateTimeField()
    ende_dt = models.DateTimeField()
    beschreibung = models.TextField(blank=True)

    fahrzeuge = models.ManyToManyField(Fahrzeug, through="DienstFahrzeug", blank=True)
    # geändert: Through für Abrollbehälter wie beim Einsatz
    abrollbehaelter = models.ManyToManyField(Abrollbehaelter, through="DienstAbrollbehaelter", blank=True)
    anhaenger = models.ManyToManyField(Anhaenger, through="DienstAnhaenger", blank=True)
    teilnahmen = models.ManyToManyField(Mitglied, through="DienstTeilnahme", related_name="dienst_teilnahmen", blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["year", "seq"], name="unique_dienst_year_seq")]
        ordering = ["-year", "-seq"]

    @property
    def nummer_formatiert(self):
        return f"{self.seq:03d}/{self.year}"

    def clean(self):
        if self.start_dt and self.ende_dt and self.start_dt >= self.ende_dt:
            raise ValidationError("Ende muss nach Beginn liegen.")

    @property
    def teilnehmer_anzahl(self):
        return self.dienstteilnahme_set.count()

    @property
    def teilnehmer_hauptamtlich(self):
        return self.dienstteilnahme_set.filter(mitglied__hauptamtlich=True).count()

    @property
    def teilnehmer_ehrenamtlich(self):
        return self.teilnehmer_anzahl - self.teilnehmer_hauptamtlich

    @property
    def dauer_stunden(self):
        if self.start_dt and self.ende_dt:
            delta = self.ende_dt - self.start_dt
            return round((delta.total_seconds() / 3600.0), 2)
        return 0.0

    @property
    def gesamtstunden(self):
        return round(self.dauer_stunden * self.teilnehmer_anzahl, 2)

    @property
    def summe_kilometer(self):
        df_km = self.dienstfahrzeug_set.aggregate(s=Sum("kilometer"))["s"] or 0
        da_km = self.dienstanhaenger_set.aggregate(s=Sum("kilometer"))["s"] or 0
        return (df_km or 0) + (da_km or 0)

    @property
    def summe_fahrzeugstunden(self):
        df_st = self.dienstfahrzeug_set.aggregate(s=Sum("stunden"))["s"] or 0
        da_st = self.dienstanhaenger_set.aggregate(s=Sum("stunden"))["s"] or 0
        return float(df_st or 0) + float(da_st or 0)

class DienstFahrzeug(models.Model):
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE)
    fahrzeug = models.ForeignKey(Fahrzeug, on_delete=models.PROTECT)
    kilometer = models.PositiveIntegerField(null=True, blank=True)
    stunden = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [("dienst", "fahrzeug")]

class DienstAbrollbehaelter(models.Model):
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE)
    abrollbehaelter = models.ForeignKey(Abrollbehaelter, on_delete=models.PROTECT)
    erforderlich = models.BooleanField(default=False)

    class Meta:
        unique_together = [("dienst", "abrollbehaelter")]

class DienstAnhaenger(models.Model):
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE)
    anhaenger = models.ForeignKey(Anhaenger, on_delete=models.PROTECT)
    kilometer = models.PositiveIntegerField(null=True, blank=True)
    stunden = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [("dienst", "anhaenger")]

class DienstTeilnahme(models.Model):
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE)
    mitglied = models.ForeignKey(Mitglied, on_delete=models.PROTECT)
    fahrzeug_funktion = models.CharField(max_length=80, blank=True)
    agt_minuten = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [("dienst", "mitglied")]
        ordering = ["mitglied__name", "mitglied__vorname"]

    def clean(self):
        if self.agt_minuten is not None and self.agt_minuten < 0:
            raise ValidationError("AGT-Minuten dürfen nicht negativ sein.")
        if self.agt_minuten is not None and not self.mitglied.agt:
            raise ValidationError("AGT-Minuten nur für AGT-Mitglieder erlaubt.")
