from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import BaseFormSet

from .models import Mitglied

class StyledAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        css = "mt-1 w-full border rounded px-3 py-2"
        self.fields["username"].widget.attrs.update({
            "class": css,
            "placeholder": "Benutzername",
        })
        self.fields["password"].widget.attrs.update({
            "class": css,
            "placeholder": "Passwort",
        })

class TeilnahmeAlleMitgliederForm(forms.Form):
    mitglied_id = forms.IntegerField(widget=forms.HiddenInput)
    selected = forms.BooleanField(required=False, label="nimmt teil")
    fahrzeug_funktion = forms.CharField(required=False, max_length=80)
    agt_minuten = forms.IntegerField(required=False, min_value=0)


class TeilnahmeAlleMitgliederBaseFormSet(BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        member_ids = [form.cleaned_data["mitglied_id"] for form in self.forms]
        if len(member_ids) != len(set(member_ids)):
            raise forms.ValidationError("Mitglieder dürfen nicht mehrfach ausgewählt werden.")

        valid_ids = set(
            Mitglied.objects.filter(pk__in=member_ids).values_list("pk", flat=True)
        )
        if valid_ids != set(member_ids):
            raise forms.ValidationError(
                "Die Teilnehmerliste enthält ein nicht mehr verfügbares Mitglied. Bitte Seite neu laden."
            )
