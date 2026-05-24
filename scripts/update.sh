#!/usr/bin/env bash
set -euo pipefail

# Beispiel:
# APP_DIR=/srv/eidiv CHECKOUT_REF=v1.2 scripts/update.sh
APP_DIR="${APP_DIR:-/home/daniel/eidiv}"
CHECKOUT_REF="${CHECKOUT_REF:-}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
SERVICE_NAME="${SERVICE_NAME:-eidiv}"
VENV_DIR="${VENV_DIR:-$APP_DIR/env}"
PY="$VENV_DIR/bin/python"

die() {
  echo "Fehler: $*" >&2
  exit 1
}

[ -n "$CHECKOUT_REF" ] || die "CHECKOUT_REF fehlt. Beispiel: CHECKOUT_REF=v1.2 scripts/update.sh"
[ -d "$APP_DIR/.git" ] || die "Kein Git-Repository unter $APP_DIR gefunden."
[ -x "$PY" ] || die "Virtuelle Umgebung nicht gefunden: $PY"
[ -f "$APP_DIR/.env" ] || die "Environment-Datei nicht gefunden: $APP_DIR/.env. Bitte install.sh bzw. die Service-Konfiguration pruefen."

APP_USER="$(stat -c '%U' "$APP_DIR")"
id "$APP_USER" >/dev/null 2>&1 || die "Besitzer '$APP_USER' von $APP_DIR existiert nicht."

run_as_app() {
  sudo -u "$APP_USER" -- "$@"
}

run_as_app test -r "$APP_DIR/.env" || die "$APP_USER kann $APP_DIR/.env nicht lesen."
run_as_app mkdir -p "$BACKUP_DIR"

echo "[1/6] Git: fetch & checkout"
CURRENT_REF="$(git -C "$APP_DIR" rev-parse HEAD)"
run_as_app git -C "$APP_DIR" fetch --tags
run_as_app git -C "$APP_DIR" checkout "$CHECKOUT_REF"

echo "[2/6] Python-Abhaengigkeiten aktualisieren"
run_as_app "$PY" -m pip install --upgrade pip wheel --no-cache-dir
run_as_app "$PY" -m pip install -r "$APP_DIR/requirements.txt" --no-cache-dir

echo "[3/6] Datenbank sichern"
TS="$(date +"%Y%m%d-%H%M%S")"
if [ -f "$APP_DIR/db.sqlite3" ]; then
  if command -v sqlite3 >/dev/null 2>&1; then
    run_as_app sqlite3 "$APP_DIR/db.sqlite3" ".backup '$BACKUP_DIR/db-$TS.sqlite3'"
  else
    run_as_app cp "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db-$TS.sqlite3"
  fi
fi

echo "[4/6] Django migrate/collectstatic"
run_as_app "$PY" "$APP_DIR/manage.py" migrate --noinput
run_as_app "$PY" "$APP_DIR/manage.py" collectstatic --noinput

echo "[5/6] Service neu starten"
sudo systemctl restart "$SERVICE_NAME"
sleep 2
sudo systemctl status "$SERVICE_NAME" --no-pager || true

echo "[6/6] Fertig. Vorheriger Commit war: $CURRENT_REF"
echo "Rollback: CHECKOUT_REF=$CURRENT_REF APP_DIR=$APP_DIR scripts/update.sh und DB-Backup zurueckspielen, falls Migrationen betroffen waren."
