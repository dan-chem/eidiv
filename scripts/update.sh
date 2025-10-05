#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/home/daniel/eidiv}"
CHECKOUT_REF="${CHECKOUT_REF:-v1.1}"  # neuen Tag hier übergeben
BACKUP_DIR="${BACKUP_DIR:-$APP_DIR/backups}"
PY="$APP_DIR/env/bin/python"
PIP="$APP_DIR/env/bin/pip"

mkdir -p "$BACKUP_DIR"
cd "$APP_DIR"

echo "[1/6] Git: fetch & checkout"
sudo -u "$(stat -c '%U' "$APP_DIR")" git fetch --tags
CURRENT_REF=$(git rev-parse --abbrev-ref HEAD || git rev-parse HEAD)
sudo -u "$(stat -c '%U' "$APP_DIR")" git checkout "$CHECKOUT_REF"

echo "[2/6] venv deps aktualisieren"
source "$APP_DIR/env/bin/activate"
$PIP install --upgrade pip wheel --no-cache-dir
$PIP install -r requirements.txt --no-cache-dir

echo "[3/6] DB-Backup (SQLite)"
TS=$(date +"%Y%m%d-%H%M%S")
if [ -f "$APP_DIR/db.sqlite3" ]; then
  # konsistentes Backup via sqlite3 .backup (falls sqlite3 cli installiert)
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "$APP_DIR/db.sqlite3" ".backup '$BACKUP_DIR/db-$TS.sqlite3'"
  else
    cp "$APP_DIR/db.sqlite3" "$BACKUP_DIR/db-$TS.sqlite3"
  fi
fi

echo "[4/6] Django migrate/collectstatic"
$PY manage.py migrate --noinput
$PY manage.py collectstatic --noinput

echo "[5/6] Service restart"
sudo systemctl restart eidiv
sleep 2
sudo systemctl status eidiv --no-pager || true

echo "[6/6] Fertig. Vorheriger Stand war: $CURRENT_REF"
echo "Rollback: git checkout $CURRENT_REF && pip install -r requirements.txt && systemctl restart eidiv && DB-Backup zurückspielen (falls nötig)."
