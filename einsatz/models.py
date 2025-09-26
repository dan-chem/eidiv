from django.db import models

# Create your models here.
# einsatz/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import (
    Mitglied, Fahrzeug, Abrollbehaelter, Anhaenger, Zusatzstelle, Einsatzmittel,
    MeldendeStelle, Brandumfang, Brandausbreitung, Brandgut, Brandobjekt,
    Loeschwasserentnahmestelle, Schadensereignis, PersonenrettungTyp,
    Sicherheitswache, Fehlalarm, Sonstige, Ortsfeuerwehr, Einsatzstichwort
)

class Einsatz(models.Model):
    year = models.PositiveIntegerField(editable=False)
    seq = models.PositiveIntegerField(editable=False)
    # Darstellung 001/2025 via property

    stichwort = models.ForeignKey(Einsatzstichwort, on_delete=models.PROTECT)
    start_dt = models.DateTimeField()
    ende_dt = models.DateTimeField()

    einsatzleiter = models.ForeignKey(Mitglied, on_delete=models.SET_NULL, null=True, blank=True)
    einsatzleiter_text = models.CharField(max_length=120, blank=True)

    meldende_stelle = models.ForeignKey(MeldendeStelle, on_delete=models.SET_NULL, null=True, blank=True)

    # Einsatzort
    objektname = models.CharField(max_length=120, blank=True)
    strasse_hausnr = models.CharField(max_length=120, blank=True)
    plz_ort = models.CharField(max_length=120, blank=True)
    einsatzgemeinde = models.CharField(max_length=120, blank=True)
    landkreis = models.CharField(max_length=120, default="Mühldorf am Inn")

    # Brand
    brandumfang = models.ForeignKey(Brandumfang, on_delete=models.SET_NULL, null=True, blank=True)
    brandausbreitung = models.ForeignKey(Brandausbreitung, on_delete=models.SET_NULL, null=True, blank=True)
    brandgut = models.ForeignKey(Brandgut, on_delete=models.SET_NULL, null=True, blank=True)
    brandobjekt = models.ForeignKey(Brandobjekt, on_delete=models.SET_NULL, null=True, blank=True)

    # THL
    schadensereignis = models.ForeignKey(Schadensereignis, on_delete=models.SET_NULL, null=True, blank=True)
    personenrettung_typ = models.ForeignKey(PersonenrettungTyp, on_delete=models.SET_NULL, null=True, blank=True)
    personenrettung_anzahl = models.PositiveIntegerField(null=True, blank=True)
    sicherheitswache = models.ForeignKey(Sicherheitswache, on_delete=models.SET_NULL, null=True, blank=True)
    fehlalarm = models.ForeignKey(Fehlalarm, on_delete=models.SET_NULL, null=True, blank=True)
    sonstige = models.ForeignKey(Sonstige, on_delete=models.SET_NULL, null=True, blank=True)

    # Freitext
    einsatzmassnahmen = models.TextField(blank=True, verbose_name="Einsatzmaßnahmen / Verwendetes Material")

    # M2M
    zusatzstellen = models.ManyToManyField(Zusatzstelle, blank=True)
    # Throughs:
    fahrzeuge = models.ManyToManyField(Fahrzeug, through="EinsatzFahrzeug", blank=True)
    abrollbehaelter = models.ManyToManyField(Abrollbehaelter, through="EinsatzAbrollbehaelter", blank=True)
    anhaenger = models.ManyToManyField(Anhaenger, through="EinsatzAnhaenger", blank=True)
    ortsfeuerwehren = models.ManyToManyField(Ortsfeuerwehr, through="EinsatzOrtsfeuerwehr", blank=True)
    einsatzmittel = models.ManyToManyField(Einsatzmittel, through="EinsatzEinsatzmittel", blank=True)
    teilnahmen = models.ManyToManyField(Mitglied, through="EinsatzTeilnahme", related_name="einsatz_teilnahmen", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["year", "seq"], name="unique_einsatz_year_seq")]
        ordering = ["-year", "-seq"]

    def __str__(self):
        return f"Einsatz {self.nummer_formatiert}"

    @property
    def nummer_formatiert(self):
        return f"{self.seq:03d}/{self.year}"

    @property
    def dauer_minuten(self):
        if self.start_dt and self.ende_dt:
            delta = self.ende_dt - self.start_dt
            return max(int(delta.total_seconds() // 60), 0)
        return 0

    @property
    def dauer_stunden(self):
        return round(self.dauer_minuten / 60.0, 2)

    def clean(self):
        if self.start_dt and self.ende_dt and self.start_dt >= self.ende_dt:
            raise ValidationError("Einsatzende muss nach Einsatzbeginn liegen.")
        if not (self.einsatzleiter or self.einsatzleiter_text):
            raise ValidationError("Bitte Einsatzleiter (Mitglied) oder Einsatzleiter (Text) angeben.")
        if self.personenrettung_anzahl is not None and self.personenrettung_anzahl < 0:
            raise ValidationError("Personenrettung: Anzahl darf nicht negativ sein.")

class EinsatzPerson(models.Model):
    TYP_CHOICES = [
        ("geschaedigter", "Geschädigter"),
        ("kostentraeger", "Kostenträger"),
        ("eigentuerer", "Eigentümer"),
        ("verursacher", "Verursacher"),
    ]
    einsatz = models.OneToOneField(Einsatz, on_delete=models.CASCADE, related_name="person")
    typ = models.CharField(max_length=20, choices=TYP_CHOICES)
    name_vorname = models.CharField(max_length=120)
    strasse_hausnr = models.CharField(max_length=120, blank=True)
    plz_ort = models.CharField(max_length=120, blank=True)
    telefon = models.CharField(max_length=60, blank=True)
    kfz_kennz = models.CharField(max_length=30, blank=True)
    kostenbefreit = models.BooleanField(default=False)
    begruendung = models.CharField(max_length=180, blank=True)

    def clean(self):
        if self.kostenbefreit and not self.begruendung.strip():
            raise ValidationError("Begründung ist erforderlich, wenn kostenbefreit = Ja.")

class EinsatzLoeschwasser(models.Model):
    einsatz = models.ForeignKey(Einsatz, on_delete=models.CASCADE, related_name="loeschwasser")
    entnahmestelle = models.ForeignKey(Loeschwasserentnahmestelle, on_delete=models.PROTECT)
    menge = models.DecimalField(max_digits=7, decimal_places=2, null=True, blank=True, help_text="z. B. m³")

class EinsatzFahrzeug(models.Model):
    einsatz = models.ForeignKey(Einsatz, on_delete=models.CASCADE)
    fahrzeug = models.ForeignKey(Fahrzeug, on_delete=models.PROTECT)
    kilometer = models.PositiveIntegerField(null=True, blank=True)
    stunden = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    erforderlich = models.BooleanField(default=False)

    class Meta:
        unique_together = [("einsatz", "fahrzeug")]

class EinsatzAbrollbehaelter(models.Model):
    einsatz = models.ForeignKey(Einsatz, on_delete=models.CASCADE)
    abrollbehaelter = models.ForeignKey(Abrollbehaelter, on_delete=models.PROTECT)
    erforderlich = models.BooleanField(default=False)

    class Meta:
        unique_together = [("einsatz", "abrollbehaelter")]

class EinsatzAnhaenger(models.Model):
    einsatz = models.ForeignKey(Einsatz, on_delete=models.CASCADE)
    anhaenger = models.ForeignKey(Anhaenger, on_delete=models.PROTECT)
    kilometer = models.PositiveIntegerField(null=True, blank=True)
    stunden = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    erforderlich = models.BooleanField(default=False)

    class Meta:
        unique_together = [("einsatz", "anhaenger")]

class EinsatzOrtsfeuerwehr(models.Model):
    einsatz = models.ForeignKey(Einsatz, on_delete=models.CASCADE)
    ortsfeuerwehr = models.ForeignKey(Ortsfeuerwehr, on_delete=models.PROTECT)
    erforderlich = models.BooleanField(default=False)

    class Meta:
        unique_together = [("einsatz", "ortsfeuerwehr")]

class EinsatzEinsatzmittel(models.Model):
    einsatz = models.ForeignKey(Einsatz, on_delete=models.CASCADE)
    einsatzmittel = models.ForeignKey(Einsatzmittel, on_delete=models.PROTECT)
    anzahl = models.PositiveIntegerField()

    class Meta:
        unique_together = [("einsatz", "einsatzmittel")]

class EinsatzTeilnahme(models.Model):
    einsatz = models.ForeignKey(Einsatz, on_delete=models.CASCADE)
    mitglied = models.ForeignKey(Mitglied, on_delete=models.PROTECT)
    fahrzeug_funktion = models.CharField(max_length=80, blank=True)
    agt_minuten = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        unique_together = [("einsatz", "mitglied")]

    def clean(self):
        if self.agt_minuten is not None and self.agt_minuten < 0:
            raise ValidationError("AGT-Minuten dürfen nicht negativ sein.")
        if self.agt_minuten is not None and not self.mitglied.agt:
            raise ValidationError("AGT-Minuten nur für AGT-Mitglieder erlaubt.")
