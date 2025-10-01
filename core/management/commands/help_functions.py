from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from family.models import *
from faker import Faker
import random
from django.utils import timezone
from datetime import timedelta
from dotenv import load_dotenv
import os
load_dotenv()
from verbrauch.models import AktionenListe
from personals.models import Level
import subprocess
from django.utils.safestring import mark_safe

level_mapping = {
    "blutiger Anfänger": 0,
    "Anfänger": 25,
    "Neuling": 50,
    "fortgeschrittener Neuling": 100,
    "Laie": 500,
    "Fortgeschrittener": 1000,
    "Kenner": 2000,
    "Experte": 4000,
    "Doktor": 8000,
    "Professor": 10000,
    "Meister": 15000,
    "Großmeister": 20000,
    "Legende": 30000,
    "Weltstar": 50000,
    "Titan": 70000,
    "Gott": 100000,
}

aktionen_mapping = {
    "1 km Fahrrad fahren / Gehen": {
        "name": "1 km Fahrrad fahren / Gehen",
        "klimapunkte": 0.34,
        "mengeBeschreibung": "gefahrene Kilometer",
        "anmerkung": "berechnet wird die CO2-Ersparnis im Vergleich zu einer gleich langen Fahrt mit dem Auto (Benziner, Mittelklasse)",
        "source": mark_safe("<a href='https://germany.myclimate.org/de/car_calculators/new '>MyClimate</a>"),
    },

    "1 Jahr lang effizient Auto fahren": {
        "name": "1 Jahr lang effizient Auto fahren",
        "klimapunkte": 355,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Tipps: <a href='https://www.adac.de/verkehr/tanken-kraftstoff-antrieb/tipps-zum-tanken/sprit-sparen-tipps/'>ADAC</>",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "Zug statt Flug": {
        "name": "Zug statt Flug",
        "klimapunkte": 198,
        "mengeBeschreibung": "1.000 Kilometer",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang täglich eine Tasse Kaffee weniger": {
        "name": "1 Jahr lang täglich eine Tasse Kaffee weniger",
        "klimapunkte": 24.5,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang Hafermilch statt Kuhmilch": {
        "name": "1 Jahr lang Autofahrten kompensieren",
        "klimapunkte": 54.5,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",

    },

    "1 Liter Hafermilch statt Kuhmilch": {
        "name": "1 Liter Hafermilch statt Kuhmilch",
        "klimapunkte": 1,
        "mengeBeschreibung": "Liter",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang keine Lebensmittel wegschmeißen": {
        "name": "1 Jahr lang keine Lebensmittel wegschmeißen",
        "klimapunkte": 128,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Tag lang keine Lebensmittel wegschmeißen": {
        "name": "1 Tag lang keine Lebensmittel wegschmeißen",
        "klimapunkte": 0.35,
        "mengeBeschreibung": "Tage",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang vegetarisch ernähren": {
        "name": "1 Jahr lang vegetarisch ernähren",
        "klimapunkte": 900,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Zusätzlich werden weniger Antibiotika eingesetzt, die Wasserverschmutzung durch Gülle wird reduziert und das Tierwohl wird gefördert",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Tag lang vegetarisch ernähren": {
        "name": "1 Tag lang vegetarisch ernähren",
        "klimapunkte": 2.47,
        "mengeBeschreibung": "Tage",
        "anmerkung": "Zusätzlich werden weniger Antibiotika eingesetzt, die Wasserverschmutzung durch Gülle wird reduziert und das Tierwohl wird gefördert",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang kein / wenig Käse": {
        "name": "1 Jahr lang kein / wenig Käse",
        "klimapunkte": 137,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Tag lang kein / wenig Käse": {
        "name": "1 Tag lang kein / wenig Käse",
        "klimapunkte": 0.375,
        "mengeBeschreibung": "Tage",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "250 g Margarine statt Butter": {
        "name": "250 g Margarine statt Butter",
        "klimapunkte": 1.6875,
        "mengeBeschreibung": "Päckchen (250 g)",
        "anmerkung": "1 kg Butter stößt bei der Herstellung 9 kg CO2 aus, 1 kg Margarine nur 2,25",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang kalt Hände waschen": {
        "name": "1 Jahr lang kalt Hände waschen",
        "klimapunkte": 164,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Händewaschen mit kaltem Wasser hat keinen negativen Einfluss auf die Hygiene",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang nur Bio-Baumwolle kaufen": {
        "name": "1 Jahr lang nur Bio-Baumwolle kaufen",
        "klimapunkte": 20.5,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Zusätzlich zum CO2 werden auch Pestizide vermieden",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "Nur 5 Minuten lang duschen": {
        "name": "Nur 5 Minuten lang duschen",
        "klimapunkte": 0.765,
        "mengeBeschreibung": "Male",
        "anmerkung": "Verglichen mit 10 Minuten lang duschen",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang nur 5 Minuten lang duschen": {
        "name": "1 Jahr lang nur 5 Minuten lang duschen",
        "klimapunkte": 279,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Verglichen mit 10 Minuten lang duschen",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang Ökostrom verwenden": {
        "name": "1 Jahr lang Ökostrom verwenden",
        "klimapunkte": 710,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang nur bestellen, was man auch behält": {
        "name": "1 Jahr lang nur bestellen, was man auch behält",
        "klimapunkte": 2.2,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Retoure kostet etwa 370 g CO2",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang unnötige E-Mails löschen": {
        "name": "1 Jahr lang unnötige E-Mails löschen",
        "klimapunkte": 21.2,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Dadurch wird Rechenleistung bei Rechenzentren gespart",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang in kalten Nächten Vorhänge und Rolläden schließen": {
        "name": "1 Jahr lang in kalten Nächten Vorhänge und Rolläden schließen",
        "klimapunkte": 50,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Diese fungieren als Wärmepolster und sparen so Heizenenergie",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang bei nur 30°C waschen": {
        "name": "1 Jahr lang bei nur 30°C waschen",
        "klimapunkte": 7.9,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang Kühlschrank richtig einstellen": {
        "name": "1 Jahr lang Kühlschrank richtig einstellen",
        "klimapunkte": 6.4,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Tipps: Eine Temperatur von 7°C im mittleren Fach ist völlig ausreichend",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },

    "1 Jahr lang auf nur 18°C heizen": {
        "name": "1 Jahr lang auf nur 18°C heizen",
        "klimapunkte": 350,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "",
        "source": "<a href='https://um.baden-wuerttemberg.de/fileadmin/redaktion/m-um/intern/Dateien/Dokumente/2_Presse_und_Service/Publikationen/Klima/Klima-Sparbuechle-barrierefrei.pdf' target='_blank'>Klima Sparbüchle</a>",
    },
}

superuser_username = "admin"
worldwide_ranking_name = "worldwide ranking"

superuser_password = os.environ.get("SUPERUSER_PASSWORD", "")
worldwide_ranking_password = os.environ.get("WORLDWIDE_RANKING_PASSWORD", "")
worldwide_ranking_admin_password = os.environ.get("WORLDWIDE_RANKING_ADMIN_PASSWORD", "")


class Command(BaseCommand):
    help = "Erstellt die Basis-Datenbankeinträge für die Anwendung."

    def handle(self, *args, **options):
        def delete_database():
            subprocess.call('rm db.sqlite3'.split())
            subprocess.call('find . -path "*/migrations/*.py" -not -name "__init__.py" -delete'.split())
            subprocess.call('find . -path "*/migrations/*.pyc" -delete'.split())
            print("deleted databse")

        def create_database():
            subprocess.call('python manage.py makemigrations'.split())
            subprocess.call('python manage.py migrate'.split())
            print("created databse")

        def create_superuser():
            if not User.objects.filter(is_superuser=True).exists():
                User.objects.create_superuser(
                    username=superuser_username,
                    password=superuser_password
                )
                print("created superuser")

        def create_worldwide_ranking():
            if not Family.objects.filter(name=worldwide_ranking_name).exists():
                worldwide_ranking = Family.objects.create(
                    name=worldwide_ranking_name,
                    password=worldwide_ranking_password
                )
                for user in User.objects.all():
                    worldwide_ranking.members.add(user)
                print("created worldwide ranking")

        def create_aktionen():
            if not AktionenListe.objects.all().exists():
                for aktion in aktionen_mapping:
                    aktion_name = aktionen_mapping[aktion]["name"]
                    aktion_klimapunkte = aktionen_mapping[aktion]["klimapunkte"]
                    aktion_mengeBeschreibung = aktionen_mapping[aktion].get("mengeBeschreibung", None)
                    aktion_anmerkung = aktionen_mapping[aktion].get("anmerkung", None)
                    aktion_source = aktionen_mapping[aktion].get("source", None)

                    if aktion_name is None or aktion_klimapunkte is None:
                        raise ValueError(f"Aktion '{aktion}' fehlt erforderliche Felder.")

                    AktionenListe.objects.create(
                        name=aktion_name,
                        klimapunkte=aktion_klimapunkte,
                        mengeBeschreibung=aktion_mengeBeschreibung,
                        anmerkung=aktion_anmerkung if aktion_anmerkung != None else "",
                        source=aktion_source if aktion_source != None else "",
                    )
                    print("created aktion")

        def create_levels():
            if not Level.objects.all().exists():
                for level in level_mapping:
                    level_description = level
                    level_klimapunkte = level_mapping[level]
                    if level_description is None or level_klimapunkte is None:
                        raise ValueError(f"Level '{level}' fehlt erforderliche Felder.")

                    Level.objects.create(
                        description=level_description,
                        klimapunkte=level_klimapunkte
                    )
                    print("created level")

        def reset_database():
            #delete_database()
            #create_database()
            create_aktionen()
            create_levels()
            create_superuser()
            create_worldwide_ranking()

        reset_database()
