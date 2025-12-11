import pyperclip

input = """Registrieren (inkl. E-Mail)
- Benutzername ändern
- Passwort ändern
- Statement ändern
- E-Mail ändern & verifizieren
- Passwort resetten
- Login
- Aktion hinzufügen
- Aktion bearbeiten
- Family hinzufügen
- Family bearbeiten
- Family beitreten
- Family Chat
- E-Mail Einstellungen ändern
- Community hinzufügen
- Community bearbeiten
- Community beitreten
- Community Chat
- Artikel hinzufügen
- Artikel bearbeiten
- Artikel kommentieren
- Artikel Kommentar beantworten
- Artikel suchen
- Event hinzufügen
- Event bearbeiten
- Event beitreten / verlassen
- Event kommentieren
- Event Kommentar antworten
- Event suchen
- Forum Beitrag hinzufügen
- Forum Beitrag antworten
- Forum Beitrag suchen
- Geschenk hinzufügen
- Geschenk teilen
- Geschenk kommentieren
- Kerze anzünden
- Konto löschen"""
input = input.replace("\n", "").replace("-", ";")
pyperclip.copy(input)