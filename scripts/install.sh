#!/usr/bin/env bash
set -euo pipefail

# Konfiguration
APP_USER="${APP_USER:-daniel}"
APP_DIR="${APP_DIR:-/home/daniel/eidiv}"
REPO_URL="${REPO_URL:-https://your.git.server/eidiv.git}"
CHECKOUT_REF="${CHECKOUT_REF:-main}"   # z. B. v1.0.1 für Release
PY=python3
PIP_OPTS="--no-cache-dir"

sudo apt-get update
sudo apt-get install -y python3-venv libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0 libffi8 libxml2 libxslt1.1 fonts-dejavu-core git

# Projektverzeichnis
sudo -u "$APP_USER" mkdir -p "$APP_DIR"
cd "$APP_DIR"

# Code holen
if [ ! -d .git ]; then
  sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
fi
sudo -u "$APP_USER" git fetch --tags
sudo -u "$APP_USER" git checkout "$CHECKOUT_REF"

# venv
if [ ! -d env ]; then
  sudo -u "$APP_USER" $PY -m venv env
fi
source env/bin/activate
pip install --upgrade pip wheel $PIP_OPTS
pip install -r requirements.txt $PIP_OPTS

# .env anlegen, falls nicht da
if [ ! -f .env ]; then
  cp .env.example .env
  echo "Bitte .env ausfüllen: $APP_DIR/.env"
fi

# Django Schritte
$PY manage.py migrate --noinput
$PY manage.py collectstatic --noinput

# systemd Unit schreiben
SERVICE_FILE=/etc/systemd/system/eidiv.service
sudo tee "$SERVICE_FILE" >/dev/null <<'UNIT'
[Unit]
Description=EiDiV (Gunicorn)
After=network.target
Wants=network-online.target

[Service]
User=daniel
Group=www-data
WorkingDirectory=/home/daniel/eidiv
EnvironmentFile=/home/daniel/eidiv/.env
ExecStart=/home/daniel/eidiv/env/bin/python -m gunicorn eidiv.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now eidiv
sudo systemctl status eidiv --no-pager
