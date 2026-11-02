import json5
from django.contrib.auth.models import User
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from family.models import Family
from personals.models import UserErweitert
from utils.functions import WORLDWIDE_RANKING_NAME

LANGUAGE = "de"


class Command(BaseCommand):
    help = "Add company data: create users from a json5 file and add them to the worldwide ranking (no families)."

    def add_arguments(self, parser):
        parser.add_argument("json5_file", type=str, help="json5 file path")

    def handle(self, *args, **options):
        try:
            with open(options["json5_file"], encoding="utf-8") as f:
                data = json5.load(f)
        except FileNotFoundError:
            raise CommandError("File not found") from None

        short_name = data["short_name"]
        members = data["members"]

        duplicates = sorted({member for member in members if members.count(member) > 1})
        if duplicates:
            raise ValueError(f"Duplicate member names found: {', '.join(duplicates)}")
        existing = User.objects.filter(username__in=members).values_list("username", flat=True).first()
        if existing:
            raise ValueError(f"Username {existing} already exists.")

        worldwide_ranking = Family.objects.get(name=WORLDWIDE_RANKING_NAME)
        with transaction.atomic():
            for member in members:
                new_user = User.objects.create_user(username=member, password=short_name)
                UserErweitert.objects.create(user=new_user, lang=LANGUAGE)
                worldwide_ranking.members.add(new_user)
