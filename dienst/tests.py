from datetime import UTC, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Mitglied

from .models import Dienst, DienstTeilnahme
from .views import DienstForm


class DienstDisplayTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="user", password="secret")
        self.client.force_login(self.user)
        self.dienst = Dienst.objects.create(
            year=2026,
            seq=1,
            titel="Maschinistenuebung",
            start_dt=datetime(2026, 5, 22, 18, 0, tzinfo=UTC),
            ende_dt=datetime(2026, 5, 22, 20, 0, tzinfo=UTC),
            beschreibung="Pumpenbetrieb am Bach",
        )
        mitglied = Mitglied.objects.create(name="Muster", vorname="Max", agt=True)
        DienstTeilnahme.objects.create(
            dienst=self.dienst,
            mitglied=mitglied,
            fahrzeug_funktion="Fahrzeugführer",
            agt_minuten=10,
        )

    def test_detail_shows_full_information(self):
        response = self.client.get(reverse("dienst_detail", args=[self.dienst.pk]))

        self.assertContains(response, "Pumpenbetrieb am Bach")
        self.assertContains(response, "Fahrzeugführer")
        self.assertContains(response, "Fahrzeugstunden")
        self.assertContains(response, "Zurück zur Startseite")
        self.assertContains(response, "PDF speichern")
        self.assertNotContains(response, "Im Admin öffnen")
        self.assertNotContains(response, "Erforderlich")

    def test_start_page_shows_compact_information_for_recent_service(self):
        response = self.client.get(reverse("index"))

        self.assertContains(response, "Maschinistenuebung")
        self.assertNotContains(response, "Pumpenbetrieb am Bach")
        self.assertNotContains(response, "Fahrzeugführer")
        self.assertNotContains(response, "Teilnehmende")

    def test_new_form_contains_disabled_submit_loading_state(self):
        response = self.client.get(reverse("dienst_neu"))

        self.assertContains(response, "data-disable-on-submit")
        self.assertContains(response, "data-saving-button")
        self.assertContains(response, "Wird gespeichert ...")
        self.assertContains(response, 'type="time"')
        self.assertNotContains(response, "data-datetime-date")

    def test_added_resource_rows_mark_exclusive_selects(self):
        endpoints = {
            "dienst_htmx_add_fahrzeug": "fahrzeug",
            "dienst_htmx_add_anhaenger": "anhaenger",
            "dienst_htmx_add_abroll": "abrollbehaelter",
        }

        for url_name, group in endpoints.items():
            with self.subTest(group=group):
                response = self.client.get(reverse(url_name))
                self.assertContains(response, f'data-exclusive-select="{group}"')

    def test_form_combines_separate_date_and_time_inputs(self):
        form = DienstForm(data={
            "titel": "Probe",
            "start_dt_0": "2026-05-22",
            "start_dt_1": "18:15",
            "ende_dt_0": "2026-05-22",
            "ende_dt_1": "20:30",
            "beschreibung": "",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["start_dt"].hour, 18)
        self.assertEqual(form.cleaned_data["start_dt"].minute, 15)

    def test_form_still_accepts_previous_datetime_local_post_format(self):
        form = DienstForm(data={
            "titel": "Probe",
            "start_dt": "2026-05-22T18:15",
            "ende_dt": "2026-05-22T20:30",
            "beschreibung": "",
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["ende_dt"].hour, 20)
        self.assertEqual(form.cleaned_data["ende_dt"].minute, 30)

    def test_pdf_can_be_rendered_with_report_design(self):
        response = self.client.get(reverse("dienst_pdf", args=[self.dienst.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
