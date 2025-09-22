from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from family.models import *
from faker import Faker
import random
from django.utils import timezone
from datetime import timedelta
from ClimateQuest.passwords import passwords

from verbrauch.models import AktionenListe
from personals.models import Level
import subprocess

level_mapping = {
    "blutiger Anfänger": 0,
    "Anfänger": 25,
    "Neuling": 50,
    "fortgeschrittener Neuling": 100,
    "Fortgeschrittener": 200,
    "erfahrener Fortgeschrittener": 400,
    "Experte": 800,
    "Meister": 1600,
    "Großmeister": 3200,
    "Legende": 6400,
    "Gott": 12800,
}

aktionen_mapping = {
    "Fahrrad fahren": {
        "name": "Fahrrad fahren",
        "klimapunkte": 0.21,
        "mengeBeschreibung": "gefahrene Kilometer",
        "anmerkung": "statt Auto",
        "date": True
    },
    "ÖPNV nutzen": {
        "name": "ÖPNV nutzen",
        "klimapunkte": 0.11,
        "mengeBeschreibung": "gefahrene Kilometer",
        "date": True
    },
    "Festseife verwenden": {
        "name": "Festseife verwenden",
        "klimapunkte": 2.0,
        "anmerkung": "TEST",
        "date": False
    },
    "Mehrwegbecher verwenden": {
        "name": "Mehrwegbecher verwenden",
        "klimapunkte": 0.5,
        "date": False
    }
}

superuser_username = "admin"
worldwide_ranking_name = "worldwide ranking"

superuser_password = passwords["superuser_password"]
worldwide_ranking_password = passwords["worldwide_ranking_password"]
worldwide_ranking_admin_password = passwords["worldwide_ranking_admin_password"]

class Command(BaseCommand):
    help = "Erstellt die Basis-Datenbankeinträge für die Anwendung."

    def handle(self, *args, **options):
        def delete_database():
            subprocess.call('rm db.sqlite3'.split())
            subprocess.call('find . -path "*/migrations/*.py" -not -name "__init__.py" -delete'.split())
            subprocess.call('find . -path "*/migrations/*.pyc" -delete'.split())
        
        def create_database():
            subprocess.call('python manage.py makemigrations'.split())
            subprocess.call('python manage.py migrate'.split())

        def create_superuser():
            if not User.objects.filter(is_superuser=True).exists():
                User.objects.create_superuser(
                    username=superuser_username,
                    password=superuser_password
                )

        def create_worldwide_ranking():
            if not Family.objects.filter(name=worldwide_ranking_name).exists():
                worldwide_ranking = Family.objects.create(
                    name=worldwide_ranking_name,
                    password=worldwide_ranking_password
                )
                for user in User.objects.all():
                    worldwide_ranking.members.add(user)

        def create_aktionen():
            if not AktionenListe.objects.all().exists():
                for aktion in aktionen_mapping:
                    aktion_name = aktionen_mapping[aktion]["name"]
                    aktion_klimapunkte = aktionen_mapping[aktion]["klimapunkte"]
                    aktion_mengeBeschreibung = aktionen_mapping[aktion].get("mengeBeschreibung", None)
                    aktion_anmerkung = aktionen_mapping[aktion].get("anmerkung", None)
                    aktion_date = aktionen_mapping[aktion]["date"]

                    if aktion_name is None or aktion_klimapunkte is None or aktion_date is None:
                        raise ValueError(f"Aktion '{aktion}' fehlt erforderliche Felder.")
                    
                    AktionenListe.objects.create(
                        name=aktion_name,
                        klimapunkte=aktion_klimapunkte,
                        mengeBeschreibung=aktion_mengeBeschreibung,
                        anmerkung=aktion_anmerkung,
                        date=aktion_date
                    )


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

        def reset_database():
            delete_database()
            create_database()
            create_aktionen()
            create_levels()
            create_superuser()
            create_worldwide_ranking()

        reset_database()
