from django import forms
from django.contrib.auth.forms import AuthenticationForm

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