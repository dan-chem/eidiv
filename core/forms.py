from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.forms import BaseFormSet

from .models import Mitglied


class CompatibleSplitDateTimeWidget(forms.SplitDateTimeWidget):
    def value_from_datadict(self, data, files, name):
        values = super().value_from_datadict(data, files, name)
        if any(values):
            return values

        combined_value = data.get(name)
        if combined_value and "T" in combined_value:
            return combined_value.split("T", 1)
        return values


def split_datetime_local_field() -> forms.SplitDateTimeField:
    return forms.SplitDateTimeField(
        widget=CompatibleSplitDateTimeWidget(
            date_format="%Y-%m-%d",
            time_format="%H:%M",
            date_attrs={
                "type": "date",
                "class": "mt-1 border rounded px-3 py-2 mr-2",
            },
            time_attrs={
                "type": "time",
                "class": "mt-1 border rounded px-3 py-2",
                "step": "60",
            },
        ),
        input_date_formats=["%Y-%m-%d"],
        input_time_formats=["%H:%M", "%H:%M:%S"],
    )


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
