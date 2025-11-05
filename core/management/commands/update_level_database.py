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


class Command(BaseCommand):
    help = "Erstellt die Basis-Datenbankeinträge für die Anwendung."

    def handle(self, *args, **options):
        def create_levels():
            for level in Level.objects.all():
                level.delete()
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

        create_levels()
