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
