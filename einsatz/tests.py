from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import Einsatzstichwort


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
