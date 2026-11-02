import csv

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from personals.models import TreeCodes


class Command(BaseCommand):
    help = "Import tree codes from a csv file with the columns code and redeemURL"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Path to csv file")
        parser.add_argument("sponsor", type=str, help="Sponsor name or url")

    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        sponsor = options["sponsor"]
        self.stdout.write(self.style.NOTICE(f"Importiere CSV: {csv_path}, gesponsert von '{sponsor}'"))
        try:
            with open(csv_path, newline="", encoding="utf-8") as f:
                codes = [
                    TreeCodes(code=row.get("code"), redeemURL=row.get("redeemURL"), sponsor=sponsor)
                    for row in csv.DictReader(f)
                ]
        except FileNotFoundError:
            raise CommandError(f"Datei nicht gefunden: {csv_path}") from None
        except (OSError, UnicodeDecodeError, csv.Error) as error:
            raise CommandError(f"Fehler beim Import: {error}") from error

        if any(not tree.code or not tree.redeemURL for tree in codes):
            raise CommandError("Fehler beim Import: jede Zeile braucht die Spalten code und redeemURL")
        with transaction.atomic():  # all or nothing: a half imported file would be hard to repair
            TreeCodes.objects.bulk_create(codes)
        self.stdout.write(self.style.SUCCESS("Import abgeschlossen"))
