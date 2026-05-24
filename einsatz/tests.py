from datetime import UTC, datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Einsatzmittel, Einsatzstichwort

from .models import Einsatz, EinsatzEinsatzmittel, EinsatzPerson


class StichwortOptionsTests(TestCase):
    def test_option_labels_are_html_escaped(self):
        user = get_user_model().objects.create_user(username="user", password="secret")
        self.client.force_login(user)
        Einsatzstichwort.objects.create(
            code="<b>BR</b>",
            bezeichnung="<script>alert(1)</script>",
        )

        response = self.client.get(reverse("einsatz_stichwort_options"))
        content = response.content.decode()

        self.assertContains(response, "&lt;b&gt;BR&lt;/b&gt;", html=False)
        self.assertContains(response, "&lt;script&gt;alert(1)&lt;/script&gt;", html=False)
        self.assertNotIn("<script>", content)


class EinsatzDisplayTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="user", password="secret")
        self.client.force_login(self.user)
        stichwort = Einsatzstichwort.objects.create(
            code="B1",
            bezeichnung="Brand Gartenhuette",
            kategorie=Einsatzstichwort.KAT_BRAND,
        )
        self.einsatz = Einsatz.objects.create(
            year=2026,
            seq=1,
            stichwort=stichwort,
            start_dt=datetime(2026, 5, 23, 10, 0, tzinfo=UTC),
            ende_dt=datetime(2026, 5, 23, 11, 0, tzinfo=UTC),
            einsatzleiter_text="Externe Einsatzleitung",
            objektname="Lagerhalle",
            einsatzmassnahmen="Wasserversorgung hergestellt",
        )
        EinsatzPerson.objects.create(
            einsatz=self.einsatz,
            typ="geschaedigter",
            name_vorname="Erika Beispiel",
        )
        mittel = Einsatzmittel.objects.create(typ="Schlauch")
        EinsatzEinsatzmittel.objects.create(
            einsatz=self.einsatz,
            einsatzmittel=mittel,
            anzahl=3,
        )

    def test_detail_shows_full_information(self):
        response = self.client.get(reverse("einsatz_detail", args=[self.einsatz.pk]))

        self.assertContains(response, "Angaben zur Person")
        self.assertContains(response, "Erika Beispiel")
        self.assertContains(response, "Wasserversorgung hergestellt")
        self.assertContains(response, "Schlauch")
        self.assertContains(response, "Zurück zur Startseite")
        self.assertContains(response, "PDF speichern")
        self.assertNotContains(response, "Im Admin öffnen")

    def test_start_page_shows_compact_information_for_recent_operation(self):
        response = self.client.get(reverse("index"))

        self.assertContains(response, "Brand Gartenhuette")
        self.assertContains(response, "Lagerhalle")
        self.assertNotContains(response, "Erika Beispiel")
        self.assertNotContains(response, "Wasserversorgung hergestellt")
        self.assertNotContains(response, "Einsatzmittel und Maßnahmen")

    def test_start_page_excludes_future_operations(self):
        Einsatz.objects.create(
            year=2099,
            seq=1,
            stichwort=self.einsatz.stichwort,
            start_dt=datetime(2099, 5, 23, 10, 0, tzinfo=UTC),
            ende_dt=datetime(2099, 5, 23, 11, 0, tzinfo=UTC),
            einsatzleiter_text="Zukuenftig",
            objektname="Noch nicht geschehen",
        )

        response = self.client.get(reverse("index"))

        self.assertNotContains(response, "Noch nicht geschehen")

    def test_new_form_contains_disabled_submit_loading_state(self):
        response = self.client.get(reverse("einsatz_neu"))

        self.assertContains(response, "data-disable-on-submit")
        self.assertContains(response, "data-saving-button")
        self.assertContains(response, "Wird gespeichert ...")
        self.assertContains(response, 'type="time"')
        self.assertNotContains(response, "data-datetime-date")

    def test_added_resource_rows_mark_exclusive_selects(self):
        endpoints = {
            "einsatz_htmx_add_fahrzeug": "fahrzeug",
            "einsatz_htmx_add_anhaenger": "anhaenger",
            "einsatz_htmx_add_abroll": "abrollbehaelter",
        }

        for url_name, group in endpoints.items():
            with self.subTest(group=group):
                response = self.client.get(reverse(url_name))
                self.assertContains(response, f'data-exclusive-select="{group}"')

    def test_pdf_template_uses_report_design(self):
        response = self.client.get(reverse("einsatz_pdf", args=[self.einsatz.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
