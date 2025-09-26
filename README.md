# Übersicht der Befehle
```
git init
git remote add origin https://github.com/dan-chem/eidiv.git
git add .

python3 -m venv env
source env/bin/activate

python -m pip install Django
pip install --upgrade pip setuptools wheel
sudo apt-get install -y libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info fonts-dejavu fonts-liberation libpangoft2-1.0-0
pip install weasyprint

python manage.py createsuperuser
```

# Übersicht der Ordnerstruktur
```
eidiv/
├─ manage.py
├─ eidiv/
│  ├─ __init__.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  └─ asgi.py
├─ core/
│  ├─ __init__.py
│  ├─ apps.py
│  ├─ admin.py        # Stammdaten-Admin
│  ├─ models.py       # Stammdaten (Mitglied, Fahrzeug, …, Einsatzstichwort, MailEmpfaenger)
│  └─ views.py        # index()
├─ einsatz/
│  ├─ __init__.py
│  ├─ apps.py
│  ├─ admin.py
│  ├─ models.py       # Einsatz + Through-Modelle, EinsatzPerson, EinsatzLoeschwasser
│  ├─ forms.py        # EinsatzForm, EinsatzPersonForm, Formsets
│  ├─ services.py     # Nummernvergabe, PDF-Render, Mailversand
│  ├─ views.py        # einsatz_neu, einsatz_detail, HTMX-Add-Zeilen
│  ├─ urls.py         # Routen der Einsatz-App
│  └─ templates/
│     └─ einsatz/
│        ├─ form.html
│        ├─ detail.html
│        ├─ pdf.html
│        ├─ _loeschwasser_row.html
│        └─ _einsatzmittel_row.html
├─ dienst/
│  ├─ __init__.py
│  ├─ apps.py
│  ├─ admin.py
│  ├─ models.py       # Dienst + Through-Modelle
│  ├─ forms.py
│  ├─ services.py     # Nummernvergabe
│  ├─ views.py        # dienst_neu, dienst_detail
│  ├─ urls.py
│  └─ templates/
│     └─ dienst/
│        ├─ form.html
│        ├─ detail.html
│        └─ pdf.html
├─ pdfs/
│  ├─ __init__.py
│  ├─ apps.py
│  └─ utils.py        # optional: WeasyPrint-Helfer
├─ templates/
│  ├─ base.html       # Gemeinsames Layout (Tailwind einbinden)
│  └─ index.html
└─ static/
   └─ pdfs/
      └─ print.css    # Druck-CSS für WeasyPrint
```