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

    "1 Jahr lang Autofahrten kompensieren": {
        "name": "1 Jahr lang Autofahrten kompensieren",
        "klimapunkte": 1393,
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

    "1.000 kWh erneuerbar heizen": {
        "name": "1.000 kWh erneuerbar heizen",
        "klimapunkte": 10,
        "mengeBeschreibung": "Jahre",
        "anmerkung": "Im Vergleich zu fossilen Brennstoffen",
        "source": "<a href='https://uba.co2-rechner.de/de_DE/calculator/housing/' target='_blank'>Umweltbundesamt Klimarechner</a>",
    },
}


class Command(BaseCommand):
    help = "Erstellt die Basis-Datenbankeinträge für die Anwendung."

    def handle(self, *args, **options):
        def create_aktionen():
            done_aktionen = []
            for aktion_key, aktion_data in aktionen_mapping.items():
                if AktionenListe.objects.filter(name=aktion_data["name"]).exists():
                    aktion_instance = AktionenListe.objects.get(name=aktion_data["name"])
                    if aktion_instance.name != aktion_data["name"]:
                        aktion_instance.name = aktion_data["name"]
                    if aktion_instance.klimapunkte != aktion_data["klimapunkte"]:
                        aktion_instance.klimapunkte = aktion_data["klimapunkte"]
                    if aktion_instance.mengeBeschreibung != aktion_data["mengeBeschreibung"]:
                        aktion_instance.mengeBeschreibung = aktion_data["mengeBeschreibung"]
                    if aktion_instance.anmerkung != aktion_data["anmerkung"]:
                        aktion_instance.anmerkung = aktion_data["anmerkung"]
                    if aktion_instance.source != aktion_data["source"]:
                        aktion_instance.source = aktion_data["source"]
                    aktion_instance.save()
                    done_aktionen.append(aktion_key)

            for aktion_key, aktion_data in aktionen_mapping.items():
                if aktion_key not in done_aktionen:
                    AktionenListe.objects.create(
                        name=aktion_data["name"],
                        klimapunkte=aktion_data["klimapunkte"],
                        mengeBeschreibung=aktion_data["mengeBeschreibung"],
                        anmerkung=aktion_data["anmerkung"] or "",
                        source=aktion_data["source"] or "",
                    )

        create_aktionen()
