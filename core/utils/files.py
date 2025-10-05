# core/utils/files.py
def safe_filename(name: str) -> str:
    # Ersetzt problematische Pfadtrenner durch Unterstrich.
    # Primär gewünscht: Slash → Unterstrich.
    # Backslash wird der Vollständigkeit halber ebenfalls ersetzt.
    return str(name).replace("/", "_").replace("\\", "_").strip()
