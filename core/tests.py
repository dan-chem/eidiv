from django.contrib.auth import get_user_model
from django.forms import formset_factory
from django.test import TestCase
from django.urls import reverse

from .forms import TeilnahmeAlleMitgliederBaseFormSet, TeilnahmeAlleMitgliederForm
from .models import Mitglied


class MitgliedAgtApiTests(TestCase):
    def test_api_requires_login(self):
        response = self.client.get(reverse("api_mitglied_agt", args=[1]))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_authenticated_user_can_read_agt_status(self):
        user = get_user_model().objects.create_user(username="user", password="secret")
        mitglied = Mitglied.objects.create(name="Muster", vorname="Max", agt=True)
        self.client.force_login(user)

        response = self.client.get(reverse("api_mitglied_agt", args=[mitglied.pk]))

        self.assertJSONEqual(response.content, {"agt": True})


class TeilnahmeAlleMitgliederFormSetTests(TestCase):
    def setUp(self):
        self.formset_cls = formset_factory(
            TeilnahmeAlleMitgliederForm,
            formset=TeilnahmeAlleMitgliederBaseFormSet,
            extra=0,
        )

    def test_unknown_member_id_is_rejected(self):
        formset = self.formset_cls(data={
            "form-TOTAL_FORMS": "1",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-mitglied_id": "9999",
            "form-0-selected": "on",
        })

        self.assertFalse(formset.is_valid())
        self.assertIn("nicht mehr verfügbares Mitglied", str(formset.non_form_errors()))

    def test_duplicate_member_id_is_rejected(self):
        mitglied = Mitglied.objects.create(name="Muster", vorname="Max")
        data = {
            "form-TOTAL_FORMS": "2",
            "form-INITIAL_FORMS": "0",
            "form-MIN_NUM_FORMS": "0",
            "form-MAX_NUM_FORMS": "1000",
            "form-0-mitglied_id": str(mitglied.pk),
            "form-1-mitglied_id": str(mitglied.pk),
        }

        formset = self.formset_cls(data=data)

        self.assertFalse(formset.is_valid())
        self.assertIn("nicht mehrfach", str(formset.non_form_errors()))
