# ClimateQuest - Allgemeines

Dieses Projekt ist eine Django Webanwendung, die Nutzerinnen und Nutzer dazu motiviert, mehr für den Klimaschutz zu tun, und zusätzlich Wissen zu dieser Thematik verbreitet. Die App ist unter [https://climate-quest.de](https://climate-quest.de) verfügbar. Weitere Informationen zu der Funktionsweise der App findest du [hier](https://climate-quest.de/artikel/artikel_detail/5). 

# Lokale Installation

Wenn du das Projekt lokal ausführen odeer bearbeiten möchtest, folge dieser Anleitung. Sie erklärt Schritt für Schritt, ...

- wie du das Projekt lokal einrichtest  
- wie du eine virtuelle Umgebung erstellst  
- wie du alle Abhängigkeiten installierst  
- wie du die Datenbank vorbereitest  
- wie du den lokalen Server startest  

**Beachte allerdings, dass dieses Projekt nicht für externe Mitarbeit gedacht ist. Daher bitte keine Pull Requests, Issues oder Feature‑Vorschläge einreichen. Feedback und Verbesserungsvorschläge können allerdings gerne unter [diesem Formular](https://docs.google.com/forms/d/e/1FAIpQLSdRLG2HmXiJ0cT74Tfd1EmOPguJHS7xLNngVFjQY5BVKcD8mA/viewform) gegeben werden. **

---

## Voraussetzungen

Um das Projekt auszuführen, benötigst du:

| Komponente | Erklärung |
|-----------|-----------|
| **Python 3.10+** | Django benötigt eine moderne Python-Version |
| **pip** | Installiert die Python-Abhängigkeiten |
| **virtualenv / venv** | Sorgt für eine isolierte Entwicklungsumgebung |
| **SQLite** | Standard-Datenbank, keine Installation nötig |

---

## Projekt herunterladen

Klonen des Repositories:

```bash
git clone https://github.com/<dein-username>/<dein-repo>.git
cd <dein-repo>
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

## Umgebungsvariablen konfigurieren

Erstelle eine Datei `.env` im Hauptverzeichnis:

```
DEBUG=True
SECRET_KEY=dein-geheimer-schluessel
DATABASE_URL=sqlite:///db.sqlite3
```

**Warum?**  
Django benötigt diese Werte, um korrekt zu starten.  
Der `SECRET_KEY` ist essenziell für Sessions und kryptografische Funktionen.

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

## Projektstruktur (Beispiel)

```
├── manage.py
├── requirements.txt
├── projectname/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── appname/
    ├── models.py
    ├── views.py
    ├── urls.py
    └── templates/
```

**Warum?**  
Damit du dich im Projekt zurechtfindest und weißt, wo welche Logik liegt.

---

## Hinweise zu Beiträgen

Dieses Repository ist **nicht** für externe Mitarbeit gedacht.  
Bitte keine Pull Requests, Issues oder Feature‑Vorschläge einreichen.

---

## Lizenz

Die Lizenz findest du in der Datei `LICENSE` im Projektverzeichnis.
