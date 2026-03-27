import csv
from django.core.management.base import BaseCommand, CommandError
from personals.models import TreeCodes


class Command(BaseCommand):
    help = 'Import tree codes from a csv file'

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Path to csv file')
        parser.add_argument('sponsor', type=str, help='Sponsor name or url')

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        sponsor = options['sponsor']

        self.stdout.write(self.style.NOTICE(f"Importiere CSV: {csv_path}, gesponsert von '{sponsor}'"))


        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # Beispiel: Spalten auslesen
                    code = row.get("code")
                    redeemURL = row.get("redeemURL")

                    # In DB speichern
                    TreeCodes.objects.create(
                        code=code,
                        redeemURL=redeemURL,
                        sponsor=sponsor,
                    )

        except FileNotFoundError:
            raise CommandError(f"Datei nicht gefunden: {csv_path}")

        except Exception as e:
            raise CommandError(f"Fehler beim Import: {e}")

        self.stdout.write(self.style.SUCCESS("Import abgeschlossen"))