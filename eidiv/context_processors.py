import os
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def git_tag(request):
    """Context-processor: stellt die aktuelle Git-Tag-Version zur Verfügung.

    Versucht zuerst, die Umgebungsvariable `GIT_TAG` zu lesen (für Deployments ohne .git).
    Falls nicht gesetzt, wird im Repository `git describe --tags --abbrev=0` ausgeführt.
    Bei Fehlern wird ein leerer String geliefert.
    """
    tag = os.environ.get("GIT_TAG") or os.environ.get("VERSION")
    if not tag:
        try:
            # Führe git describe im Projekt-Root aus
            tag = subprocess.check_output(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=BASE_DIR,
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except Exception:
            tag = ""
    return {"GIT_TAG": tag}
