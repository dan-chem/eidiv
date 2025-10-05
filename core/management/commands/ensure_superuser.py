# core/management/commands/ensure_superuser.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os, secrets

class Command(BaseCommand):
    help = "Erstellt einen Superuser, falls keiner existiert (idempotent). Nutzt ENV-Variablen."

    def add_arguments(self, parser):
        parser.add_argument("--username", default=os.environ.get("ADMIN_USERNAME", "admin"))
        parser.add_argument("--email", default=os.environ.get("ADMIN_EMAIL", "admin@example.com"))
        parser.add_argument("--password", default=os.environ.get("ADMIN_PASSWORD"))

    def handle(self, *args, **opts):
        User = get_user_model()
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write(self.style.SUCCESS("Superuser existiert bereits – nichts zu tun."))
            return

        username = opts["username"]
        email = opts["email"]
        password = opts["password"] or os.environ.get("DJANGO_SUPERUSER_PASSWORD")

        if not password:
            password = secrets.token_urlsafe(16)
            self.stdout.write(self.style.WARNING(
                f"Kein Passwort in ENV/Args gefunden. Generiere eines:\n  Benutzer: {username}\n  Passwort: {password}"
            ))

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' angelegt."))
