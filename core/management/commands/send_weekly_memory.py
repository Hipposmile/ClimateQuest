from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from verbrauch.models import *
from utils.functions import *
from datetime import timedelta
from django.test import RequestFactory

factory = RequestFactory()
fake_request = factory.get('/')

class Command(BaseCommand):
    help = "Weekly Cronjobs"


    def handle(self, *args, **options):
        def create_reminder():
            for user in User.objects.all():
                try:
                    if not Aktion.objects.filter(user=user, date__gte=timezone.now().date() - timedelta(days=7)).exists():
                        fake_request = fake_request.user = user
                        create_notification(fake_request, notification=f"Hey {user.username}, du hast in der letzten Woche keine einzige Aktion eingetragen! Ändere das und schütze nicht nur das Klima, sondern steige auch in den Rankings deiner Families und Communities sowie in deinem Level auf!", user=user)
                except Exception as e:
                    error_message = f'Cronjob: {timezone.now().isoformat()} Create Reminder for User: {user}: Exception: {e}'
                    with open('logs/errors.log', 'a') as file:
                        file.write(f'{error_message}\n\n')

        def main():
            create_reminder()
        
        main()