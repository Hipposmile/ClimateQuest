from django.contrib.auth.models import User
from django.core.management import BaseCommand
import json5
from community.models import Community
from family.models import Family
from personals.models import UserErweitert

LANGUAGE = "de"


class Command(BaseCommand):
    help = 'Add company data: Create users, families and community. Users will not be added to families.'

    def add_arguments(self, parser):
        parser.add_argument('json5_file', type=str, help='json5 file path')

    def handle(self, *args, **options):
        json5_file = options['json5_file']

        try:
            with open(json5_file, "r", encoding="utf-8") as f:
                data = json5.load(f)
        except FileNotFoundError:
            raise FileNotFoundError("File not found")

        name = data['name']
        short_name = data['short_name']

        community_exists = Community.objects.filter(name=name).exists()
        if community_exists:
            raise ValueError(f"Community {name} already exists.")

        groups = data['groups']
        seen_groups = set()
        duplicate_groups = set()
        for g in groups:
            group_name_exists = Family.objects.filter(name=f"{g} ({short_name})").exists()
            if group_name_exists:
                raise ValueError(f"Family {g} already exists.")
            if g in seen_groups:
                duplicate_groups.add(g)
            seen_groups.add(g)
        if duplicate_groups:
            raise ValueError(f"Duplicate member names found: {', '.join(duplicate_groups)}")

        members = data['members']
        seen_members = set()
        duplicate_members = set()
        for m in members:
            user_exists = User.objects.filter(username=m).exists()
            if user_exists:
                raise ValueError(f"Username {m} already exists.")
            if m in seen_members:
                duplicate_members.add(m)
            seen_members.add(m)
        if duplicate_members:
            raise ValueError(f"Duplicate member names found: {', '.join(duplicate_members)}")

        #community = Community.objects.create(name=name, password=short_name, admin_password=short_name)

        #for group in groups:
            family = Family.objects.create(name=f"{group} ({short_name})", password=short_name,
                                           admin_password=short_name)
            community.members.add(family)

        family_worldwide_ranking = Family.objects.get(name="worldwide ranking")

        for member in members:
            new_user = User.objects.create_user(username=member, password=short_name)
            UserErweitert.objects.create(user=new_user, lang=LANGUAGE)
            family_worldwide_ranking.members.add(new_user)
