# EiDiV

## Erstinstallation

Das Skript installiert Systempakete, legt die Python-Umgebung an, initialisiert
Django und schreibt die systemd-Unit passend zu `APP_USER` und `APP_DIR`.

```bash
git clone https://github.com/dan-chem/eidiv.git
cd eidiv
APP_USER=daniel APP_DIR=/home/daniel/eidiv CHECKOUT_REF=master scripts/install.sh
```

Die Variablen können für eine andere Installation angepasst werden, zum
Beispiel `APP_USER=eidiv APP_DIR=/srv/eidiv`. Die erzeugte Unit verwendet
dann genau dieses Verzeichnis und erwartet die Datei `$APP_DIR/.env`.

Beim ersten Lauf wird `.env.example` als `.env` angelegt und ein zufälliger
`SECRET_KEY` ergänzt. Ist `ADMIN_PASSWORD` leer, erzeugt das Skript beim
Anlegen des ersten Admin-Kontos ein zufälliges Passwort und gibt es einmalig
im Terminal aus. Vor dem Produktivbetrieb müssen insbesondere Hosts und
SMTP-Zugangsdaten in `.env` geprüft werden.

Nützliche optionale Variablen:

```bash
APP_GROUP=www-data SERVICE_NAME=eidiv VENV_DIR=/home/daniel/eidiv/env scripts/install.sh
```

## Update

Updates erwarten eine vorhandene Installation, `.env` und virtuelle Umgebung.
Die Django-Schritte und das Datenbank-Backup laufen als Besitzer des
Anwendungsverzeichnisses, damit SQLite- und Static-Dateirechte konsistent
bleiben.

```bash
APP_DIR=/home/daniel/eidiv CHECKOUT_REF=vX.Y scripts/update.sh
```

Das Skript legt vor Migrationen eine Sicherung von `db.sqlite3` unter
`$APP_DIR/backups/` an und startet anschließend den Service neu.

## Fehlerdiagnose

Wenn systemd meldet, dass die Environment-Datei nicht gefunden wurde:

```bash
systemctl cat eidiv
ls -l /home/daniel/eidiv/.env
```

`WorkingDirectory`, `EnvironmentFile` und `ExecStart` in der Unit müssen zum
tatsächlich installierten `APP_DIR` passen. Bei einer Unit aus einer älteren
Installation kann `install.sh` mit den korrekten Variablen erneut ausgeführt
werden; `.env` wird dabei nicht überschrieben und eine vorhandene Datenbank
vor Migrationen unter `$APP_DIR/backups/` gesichert.
