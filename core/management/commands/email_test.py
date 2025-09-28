from django.core.management.base import BaseCommand
from django.utils import timezone
from core.services.mail import send_mail_with_pdf_to_active, send_mail_text
from core.services.mail import get_active_recipients

class Command(BaseCommand):
    help = "Sendet eine Test-E-Mail an alle aktiven Empfänger"

    def add_arguments(self, parser):
        parser.add_argument("--with-pdf", action="store_true", help="kleinen PDF-Anhang mitsenden")

    def handle(self, *args, **opts):
        recipients = get_active_recipients()
        if not recipients:
            self.stdout.write(self.style.WARNING("Keine aktiven Empfänger definiert."))
            return

        now = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        subject = "EiDiV Test-E-Mail"
        body = f"Dies ist eine Test-E-Mail aus EiDiV ({now}). Empfängeranzahl: {len(recipients)}"

        if opts["with_pdf"]:
            # Minimal-PDF (einfacher Byte-Array; in echt gern via WeasyPrint generieren)
            pdf_bytes = b"%PDF-1.4\n% Test\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
            sent = send_mail_with_pdf_to_active(subject, body, pdf_bytes, "test.pdf", fail_silently=False)
        else:
            sent = send_mail_text(subject, body, bcc=recipients, fail_silently=False)

        self.stdout.write(self.style.SUCCESS(f"Versendet: {sent}"))
