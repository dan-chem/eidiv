from django.contrib import admin
from .models import (
    Mitglied, Fahrzeug, Abrollbehaelter, Anhaenger, Zusatzstelle, Einsatzmittel,
    MeldendeStelle, Brandumfang, Brandausbreitung, Brandgut, Brandobjekt,
    Loeschwasserentnahmestelle, Schadensereignis, PersonenrettungTyp,
    Sicherheitswache, Fehlalarm, Sonstige, Ortsfeuerwehr, Einsatzstichwort, MailEmpfaenger
)

for m in [Mitglied, Fahrzeug, Abrollbehaelter, Anhaenger, Zusatzstelle, Einsatzmittel, MeldendeStelle,
          Brandumfang, Brandausbreitung, Brandgut, Brandobjekt, Loeschwasserentnahmestelle,
          Schadensereignis, PersonenrettungTyp, Sicherheitswache, Fehlalarm, Sonstige, Ortsfeuerwehr,
          Einsatzstichwort, MailEmpfaenger]:
    admin.site.register(m)
