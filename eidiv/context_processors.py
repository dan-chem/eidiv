import os

from core import __version__


def git_tag(request):
    """Stellt die sichtbare Release-Version fuer den Seitenkopf bereit.

    Deployments koennen die Anzeige weiterhin explizit per Umgebungsvariable
    ueberschreiben. Ohne Override wird die Version aus dem Anwendungscode
    verwendet, damit die Anzeige nicht von vorhandenen Git-Metadaten abhaengt.
    """
    tag = os.environ.get("GIT_TAG") or os.environ.get("VERSION") or f"v{__version__}"
    return {"GIT_TAG": tag}
