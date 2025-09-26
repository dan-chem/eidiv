from django.db import models

# Create your models here.
# dienst/models.py
from django.core.exceptions import ValidationError
from django.db import models
from core.models import Mitglied, Fahrzeug, Abrollbehaelter, Anhaenger

class Dienst(models.Model):
    year = models.PositiveIntegerField(editable=False)
    seq = models.PositiveIntegerField(editable=False)
    titel = models.CharField(max_length=160)
    start_dt = models.DateTimeField()
    ende_dt = models.DateTimeField()
    beschreibung = models.TextField(blank=True)

    fahrzeuge = models.ManyToManyField(Fahrzeug, through="DienstFahrzeug", blank=True)
    abrollbehaelter = models.ManyToManyField(Abrollbehaelter, blank=True)  # keine Zusatzfelder
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

class DienstFahrzeug(models.Model):
    dienst = models.ForeignKey(Dienst, on_delete=models.CASCADE)
    fahrzeug = models.ForeignKey(Fahrzeug, on_delete=models.PROTECT)
    kilometer = models.PositiveIntegerField(null=True, blank=True)
    stunden = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = [("dienst", "fahrzeug")]

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

    def clean(self):
        if self.agt_minuten is not None and self.agt_minuten < 0:
            from django.core.exceptions import ValidationError
            raise ValidationError("AGT-Minuten dürfen nicht negativ sein.")
        if self.agt_minuten is not None and not self.mitglied.agt:
            from django.core.exceptions import ValidationError
            raise ValidationError("AGT-Minuten nur für AGT-Mitglieder erlaubt.")
