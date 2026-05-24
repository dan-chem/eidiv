#!/usr/bin/env bash
set -euo pipefail

# Konfiguration, bei Bedarf beim Aufruf ueberschreiben:
# APP_USER=eidiv APP_DIR=/srv/eidiv CHECKOUT_REF=v1.2 scripts/install.sh
APP_USER="${APP_USER:-daniel}"
APP_DIR="${APP_DIR:-/home/$APP_USER/eidiv}"
APP_GROUP="${APP_GROUP:-}"
REPO_URL="${REPO_URL:-https://github.com/dan-chem/eidiv.git}"
CHECKOUT_REF="${CHECKOUT_REF:-master}"
SERVICE_NAME="${SERVICE_NAME:-eidiv}"
VENV_DIR="${VENV_DIR:-$APP_DIR/env}"
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PIP_OPTS=(--no-cache-dir)

die() {
  echo "Fehler: $*" >&2
  exit 1
}

run_as_app() {
  sudo -u "$APP_USER" -- "$@"
}

id "$APP_USER" >/dev/null 2>&1 || die "Benutzer '$APP_USER' existiert nicht."
case "$APP_DIR:$VENV_DIR" in
  *[[:space:]]*) die "APP_DIR und VENV_DIR duerfen fuer die systemd-Unit keine Leerzeichen enthalten." ;;
esac
if [ -z "$APP_GROUP" ]; then
  APP_GROUP="$(id -gn "$APP_USER")"
fi
getent group "$APP_GROUP" >/dev/null 2>&1 || die "Gruppe '$APP_GROUP' existiert nicht."

echo "[1/7] Systempakete installieren"
sudo apt-get update
sudo apt-get install -y \
  python3-venv libcairo2 libpango-1.0-0 libgdk-pixbuf2.0-0 libffi-dev \
  shared-mime-info fonts-dejavu fonts-liberation libpangoft2-1.0-0 git

echo "[2/7] Code bereitstellen: $APP_DIR"
sudo install -d -o "$APP_USER" -g "$APP_GROUP" "$APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
  if [ -n "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]; then
    die "$APP_DIR ist nicht leer und enthaelt kein Git-Repository."
  fi
  run_as_app git clone "$REPO_URL" "$APP_DIR"
fi
run_as_app git -C "$APP_DIR" fetch --tags
run_as_app git -C "$APP_DIR" checkout "$CHECKOUT_REF"

echo "[3/7] Virtuelle Python-Umgebung und Abhaengigkeiten"
if [ ! -x "$VENV_DIR/bin/python" ]; then
  run_as_app "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
sudo chown -R "$APP_USER:$APP_GROUP" "$VENV_DIR"
run_as_app "$VENV_DIR/bin/python" -m pip install --upgrade pip wheel "${PIP_OPTS[@]}"
run_as_app "$VENV_DIR/bin/python" -m pip install -r "$APP_DIR/requirements.txt" "${PIP_OPTS[@]}"

echo "[4/7] Umgebungskonfiguration pruefen"
if [ ! -f "$APP_DIR/.env" ]; then
  run_as_app cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  echo "Neue Konfiguration angelegt: $APP_DIR/.env"
  echo "Bitte SMTP-, Host- und Admin-Werte vor dem Produktivbetrieb pruefen."
fi
sudo chown "$APP_USER:$APP_GROUP" "$APP_DIR/.env"
run_as_app test -r "$APP_DIR/.env" || die "$APP_USER kann $APP_DIR/.env nicht lesen."
run_as_app chmod 600 "$APP_DIR/.env"
if ! run_as_app grep -Eq '^SECRET_KEY=.+$' "$APP_DIR/.env"; then
  SECRET_KEY="$(run_as_app "$VENV_DIR/bin/python" -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
  printf '\nSECRET_KEY="%s"\n' "$SECRET_KEY" | sudo -u "$APP_USER" tee -a "$APP_DIR/.env" >/dev/null
  echo "Zufaelliger SECRET_KEY wurde in $APP_DIR/.env ergaenzt."
fi

echo "[5/7] Django initialisieren"
for runtime_path in "$APP_DIR/db.sqlite3" "$APP_DIR/staticfiles" "$APP_DIR/media" "$BACKUP_DIR"; do
  if [ -e "$runtime_path" ]; then
    sudo chown -R "$APP_USER:$APP_GROUP" "$runtime_path"
  fi
done
if [ -f "$APP_DIR/db.sqlite3" ]; then
  run_as_app mkdir -p "$BACKUP_DIR"
  TS="$(date +"%Y%m%d-%H%M%S")"
  if command -v sqlite3 >/dev/null 2>&1; then
    run_as_app sqlite3 "$APP_DIR/db.sqlite3" ".backup '$BACKUP_DIR/db-before-install-$TS.sqlite3'"
  else
    run_as_app cp "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db-before-install-$TS.sqlite3"
  fi
  echo "Bestehende Datenbank gesichert: $BACKUP_DIR/db-before-install-$TS.sqlite3"
fi
run_as_app "$VENV_DIR/bin/python" "$APP_DIR/manage.py" migrate --noinput
run_as_app "$VENV_DIR/bin/python" "$APP_DIR/manage.py" collectstatic --noinput
run_as_app "$VENV_DIR/bin/python" "$APP_DIR/manage.py" ensure_superuser

echo "[6/7] systemd-Unit schreiben"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
sudo tee "$SERVICE_FILE" >/dev/null <<UNIT
[Unit]
Description=EiDiV (Gunicorn)
After=network.target
Wants=network-online.target

[Service]
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/.env
ExecStart=$VENV_DIR/bin/python -m gunicorn eidiv.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

echo "[7/7] Dienst starten"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager
