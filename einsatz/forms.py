# einsatz/forms.py
from django import forms
from django.forms import inlineformset_factory

from .models import (
    Einsatz, EinsatzPerson, EinsatzLoeschwasser, EinsatzEinsatzmittel,
    EinsatzFahrzeug, EinsatzAbrollbehaelter, EinsatzAnhaenger, EinsatzOrtsfeuerwehr, EinsatzZusatzstelle, 
    EinsatzTeilnahme
)

class EinsatzForm(forms.ModelForm):
    class Meta:
        model = Einsatz
        fields = [
            "stichwort", "start_dt", "ende_dt",
            "einsatzleiter", "einsatzleiter_text", "meldende_stelle",
            "objektname", "strasse_hausnr", "plz_ort", "einsatzgemeinde", "landkreis",
            "brandumfang", "brandausbreitung", "brandgut", "brandobjekt",
            "schadensereignis", "personenrettung_typ", "personenrettung_anzahl",
            "sicherheitswache", "fehlalarm", "sonstige", "einsatzmassnahmen",
        ]
        widgets = {
            "stichwort": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "start_dt": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "mt-1 w-full border rounded px-3 py-2"}),
            "ende_dt": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "mt-1 w-full border rounded px-3 py-2"}),
            "einsatzleiter": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "einsatzleiter_text": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "meldende_stelle": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "objektname": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "strasse_hausnr": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "plz_ort": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "einsatzgemeinde": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "landkreis": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),

            "brandumfang": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "brandausbreitung": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "brandgut": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "brandobjekt": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),

            "schadensereignis": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "personenrettung_typ": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "personenrettung_anzahl": forms.NumberInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2", "min": 0}),
            "sicherheitswache": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "fehlalarm": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "sonstige": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),

            "einsatzmassnahmen": forms.Textarea(attrs={"class": "mt-1 w-full border rounded px-3 py-2", "rows": 6}),
        }

class EinsatzPersonForm(forms.ModelForm):
    class Meta:
        model = EinsatzPerson
        fields = ["typ", "name_vorname", "strasse_hausnr", "plz_ort", "telefon", "kfz_kennz", "kostenbefreit", "begruendung"]
        widgets = {
            "typ": forms.Select(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "name_vorname": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "strasse_hausnr": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "plz_ort": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "telefon": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "kfz_kennz": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
            "kostenbefreit": forms.CheckboxInput(attrs={"class": "mt-1"}),
            "begruendung": forms.TextInput(attrs={"class": "mt-1 w-full border rounded px-3 py-2"}),
        }

LoeschwasserFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzLoeschwasser,
    fields=["entnahmestelle", "menge"],
    widgets={
        "entnahmestelle": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
        "menge": forms.NumberInput(attrs={"class": "w-full border rounded px-2 py-1", "step": "0.01", "min": 0}),
    },
    extra=0,
    can_delete=True,
)

EinsatzmittelFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzEinsatzmittel,
    fields=["einsatzmittel", "anzahl"],
    widgets={
        "einsatzmittel": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
        "anzahl": forms.NumberInput(attrs={"class": "w-full border rounded px-2 py-1", "min": 0}),
    },
    extra=0,
    can_delete=True,
)

EinsatzFahrzeugFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzFahrzeug,
    fields=["fahrzeug", "kilometer", "stunden", "erforderlich"],
    widgets={
        "fahrzeug": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
        "kilometer": forms.NumberInput(attrs={"class": "w-full border rounded px-2 py-1", "min": 0}),
        "stunden": forms.NumberInput(attrs={"class": "w-full border rounded px-2 py-1", "step": "0.01", "min": 0}),
    },
    extra=0,
    can_delete=True,
)

EinsatzAbrollFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzAbrollbehaelter,
    fields=["abrollbehaelter", "erforderlich"],
    widgets={
        "abrollbehaelter": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
    },
    extra=0,
    can_delete=True,
)

EinsatzAnhaengerFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzAnhaenger,
    fields=["anhaenger", "kilometer", "stunden", "erforderlich"],
    widgets={
        "anhaenger": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
        "kilometer": forms.NumberInput(attrs={"class": "w-full border rounded px-2 py-1", "min": 0}),
        "stunden": forms.NumberInput(attrs={"class": "w-full border rounded px-2 py-1", "step": "0.01", "min": 0}),
    },
    extra=0,
    can_delete=True,
)

EinsatzOrtsfeuerwehrFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzOrtsfeuerwehr,
    fields=["ortsfeuerwehr", "erforderlich"],
    widgets={
        "ortsfeuerwehr": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
    },
    extra=0,
    can_delete=True,
)

ZusatzstelleFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzZusatzstelle,
    fields=["zusatzstelle"],
    widgets={
        "zusatzstelle": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
    },
    extra=0,
    can_delete=True,
)

EinsatzTeilnahmeFormSet = inlineformset_factory(
    parent_model=Einsatz,
    model=EinsatzTeilnahme,
    fields=["mitglied", "fahrzeug_funktion", "agt_minuten"],
    widgets={
        "mitglied": forms.Select(attrs={"class": "w-full border rounded px-2 py-1"}),
        "fahrzeug_funktion": forms.TextInput(attrs={"class": "w-full border rounded px-2 py-1"}),
        "agt_minuten": forms.NumberInput(attrs={"class": "w-full border rounded px-2 py-1", "min": 0}),
    },
    extra=0,
    can_delete=True,
)
