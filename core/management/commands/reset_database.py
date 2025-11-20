from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
import json
from django.core.serializers.json import DjangoJSONEncoder

from personals.models import UserErweitert

import sys


class Command(BaseCommand):
    help = "Speichert alle User in einem externen Dictionary und trägt sie anschließend wieder ein."

    def handle(self, *args, **options):
        def save_users():
            users = User.objects.values()
            users_dict = {u["id"]: u for u in users}

            with open("users.json", "w", encoding="utf-8") as f:
                json.dump(users_dict, f, indent=4, cls=DjangoJSONEncoder)


        def add_users():
            for user in User.objects.all():
                user.delete()
            with open("users.json", "r", encoding="utf-8") as f:
                users_dict = json.load(f)

            for user in users_dict:
                user = User.objects.create(
                    id=users_dict[user]["id"],
                    username=users_dict[user]["username"],
                    email=users_dict[user]["email"],
                    password=users_dict[user]["password"],
                    last_login=users_dict[user]["last_login"],
                    date_joined=users_dict[user]["date_joined"],
                    is_superuser=users_dict[user]["is_superuser"],
                    is_staff=users_dict[user]["is_staff"],
                    is_active=users_dict[user]["is_active"],
                    first_name=users_dict[user]["first_name"],
                    last_name=users_dict[user]["last_name"],
                )
                UserErweitert.objects.create(
                    user=user
                )

        def main():
            user_input = input('save users (s) / add users (a): ')
            if user_input == 's':
                confirm = input('this will save all users from database to users.json. Continue? (y/n): ')
                if confirm == 'y':
                    save_users()
                else:
                    sys.exit()
            elif user_input == 'a':
                confirm = input('this will delete all users from database and add the ones from users.json. Continue? (y/n): ')
                if confirm == 'y':
                    add_users()
                else:
                    sys.exit()
            else:
                print('Unbekannte Eingabe')
                main()

        main()