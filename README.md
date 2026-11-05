# ClimateQuest - Allgemeines

Dieses Projekt ist eine Django Webanwendung, die Nutzerinnen und Nutzer dazu motiviert, mehr für den Klimaschutz zu tun,
und zusätzlich Wissen zu dieser Thematik verbreitet. Die App ist
unter [https://climate-quest.de](https://climate-quest.de) verfügbar. Weitere Informationen zu der Funktionsweise der
App findest du [hier](https://climate-quest.de/artikel/artikel_detail/5).

---
---

# Lokale Installation

Wenn du das Projekt lokal ausführen odeer bearbeiten möchtest, folge dieser Anleitung. Sie erklärt Schritt für
Schritt, ...

- wie du das Projekt lokal einrichtest
- wie du eine virtuelle Umgebung erstellst
- wie du alle Abhängigkeiten installierst
- wie du die Datenbank vorbereitest
- wie du den lokalen Server startest

> [!CAUTION]
> Beachte allerdings, dass dieses Projekt nicht für externe Mitarbeit gedacht ist. Daher bitte keine Pull Requests,
Issues oder Feature‑Vorschläge einreichen. Feedback und Verbesserungsvorschläge können allerdings gerne
unter [diesem Formular](https://docs.google.com/forms/d/e/1FAIpQLSdRLG2HmXiJ0cT74Tfd1EmOPguJHS7xLNngVFjQY5BVKcD8mA/viewform)
gegeben werden.

---

## Voraussetzungen

Um das Projekt auszuführen, benötigst du:

| Komponente            | Erklärung                                     |
|-----------------------|-----------------------------------------------|
| **Python 3.10+**      | Django benötigt eine moderne Python-Version   |
| **pip**               | Installiert die Python-Abhängigkeiten         |
| **virtualenv / venv** | Sorgt für eine isolierte Entwicklungsumgebung |
| **SQLite**            | Standard-Datenbank, keine Installation nötig  |

---

## Projekt herunterladen

Klonen des Repositories:

```bash
git clone https://github.com/Hipposmile/ClimateQuest.git
cd ClimateQuest
```

**Warum?**  
Damit hast du eine lokale Kopie des Projekts, mit der du arbeiten kannst.

---

## Virtuelle Umgebung erstellen

Eine virtuelle Umgebung verhindert Versionskonflikte mit anderen Projekten.

Erstellen:

```bash
python3 -m venv venv
```

Aktivieren:

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

---

## Abhängigkeiten installieren

Alle benötigten Pakete stehen in `requirements.txt`.

```bash
pip install -r requirements.txt
```

**Warum?**  
Damit Django und alle weiteren Bibliotheken verfügbar sind.

---

## Datenbank vorbereiten

Django verwendet Migrationen, um die Datenbankstruktur zu erstellen.

```bash
python manage.py migrate
```

Optional: Admin‑Benutzer erstellen

```bash
python manage.py createsuperuser
```

**Warum?**  
Damit die Tabellen existieren und du dich im Django‑Admin anmelden kannst.

---

## Server starten

```bash
python manage.py runserver
```

Die Anwendung ist nun erreichbar unter:

```
http://127.0.0.1:8000/
```

**Warum?**  
Dies startet den integrierten Django‑Entwicklungsserver, ideal für lokale Entwicklung.

---

## Tests, Linter und Übersetzungen

Entwicklungs-Abhängigkeiten installieren (enthält pytest, coverage, ruff, polib):

```bash
pip install -r requirements-dev.txt
```

Alle Tests inklusive 100 % Coverage auf SQLite **und** PostgreSQL ausführen:

```bash
make test
```

Für PostgreSQL werden `PGHOST`, `PGPORT`, `PGUSER`, `PGPASSWORD` (und optional `PGDATABASE`) gelesen; der Benutzer
braucht das Recht, die Test-Datenbank anzulegen. Nur eine Datenbank testen: `make test-sqlite` bzw. `make test-postgres`. Zuvor ausführen: `export PGHOST=localhost PGUSER=tester PGPASSWORD=testpw123 PGDATABASE=postgres`!

```bash
make lint      # ruff check + ruff format --check
make format    # Code automatisch formatieren
```

Übersetzungen (`gettext` muss installiert sein): nach Änderungen an Texten in jedem App-Verzeichnis
`django-admin makemessages -a` ausführen, die `.po`-Dateien ergänzen und danach `python manage.py compilemessages`.
Die Tests schlagen fehl, wenn Einträge leer, `fuzzy`, veraltet oder nicht kompiliert sind.

Einstellungen: `ClimateQuest.settings` (Entwicklung), `ClimateQuest.settingsprod` (Produktion, Geheimnisse aus
Umgebungsvariablen/`.env`), `ClimateQuest.settingstest` (Tests).

---

# Energie- und CO₂-Sparmaßnahmen

- **Emoji-Schrift:** `static/fonts/OpenMoji-subset.woff2` (≈ 29 KB) enthält nur die tatsächlich verwendeten Emojis. Die
  vollständige Schrift (2,6 MB) liegt unter `tools/fonts/`. Wird irgendwo ein **neues** Emoji
  (`<span class="emoji">&#x....;</span>`) verwendet, danach `tools/subset_emoji_font.sh` ausführen
  (`pip install fonttools brotli`).
- **Bilder:** `<picture>`-Elemente nutzen korrekte `sizes`-Werte, damit nur die Bildbreite geladen wird, die wirklich
  angezeigt wird. Die PNG/JPG-Fallbacks sind klein gehalten (nur für sehr alte Browser).
- **Komprimierung:** Dynamische Seiten werden per gzip ausgeliefert, statische Dateien vorab mit Brotli/gzip (`Brotli` in
  `requirements.txt`).
- **Bibliotheken nur bei Bedarf:** Quill (Editor) und der QR-Code-Generator werden erst geladen, wenn sie gebraucht werden.
- **Dunkles Farbschema:** Bei Geräten mit aktivierter Systemeinstellung „Dunkel“ (`prefers-color-scheme: dark`) wird
  automatisch ein dunkles Farbschema genutzt (spart Strom auf OLED-Displays). Die Farben stehen als CSS-Variablen in
  `static/css/style.css`; für Hintergründe bitte `--color-surface` statt `--color-white` verwenden.
- **Startseiten-Statistik** wird 10 Minuten zwischengespeichert, Lottie-Animationen starten erst per Klick/Tap.
- **Bilder im Karussell** sind auf 1280 px Breite begrenzt.
