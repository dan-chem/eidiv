# einsatz/forms.py
from django import forms
from django.forms import inlineformset_factory
from .models import (Einsatz, EinsatzPerson, EinsatzLoeschwasser, EinsatzEinsatzmittel,
                     EinsatzTeilnahme, EinsatzFahrzeug, EinsatzAbrollbehaelter, EinsatzAnhaenger, EinsatzOrtsfeuerwehr)

class EinsatzForm(forms.ModelForm):
    class Meta:
        model = Einsatz
        fields = [
            "stichwort", "start_dt", "ende_dt",
            "einsatzleiter", "einsatzleiter_text", "meldende_stelle",
            "objektname", "strasse_hausnr", "plz_ort", "einsatzgemeinde", "landkreis",
            "brandumfang", "brandausbreitung", "brandgut", "brandobjekt",
            "schadensereignis", "personenrettung_typ", "personenrettung_anzahl",
            "sicherheitswache", "fehlalarm", "sonstige",
            "zusatzstellen", "einsatzmassnahmen",
        ]
        widgets = {
            "start_dt": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "ende_dt": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def clean(self):
        cleaned = super().clean()
        # Einsatzleiter muss FK oder Text sein – wird in model.clean() zusätzlich geprüft
        return cleaned

class EinsatzPersonForm(forms.ModelForm):
    class Meta:
        model = EinsatzPerson
        fields = ["typ", "name_vorname", "strasse_hausnr", "plz_ort", "telefon", "kfz_kennz", "kostenbefreit", "begruendung"]

LoeschwasserFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzLoeschwasser,
    fields=["entnahmestelle", "menge"],
    extra=0,
    can_delete=True,
)

EinsatzmittelFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzEinsatzmittel,
    fields=["einsatzmittel", "anzahl"],
    extra=0,
    can_delete=True,
)
