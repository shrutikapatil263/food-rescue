from django.core.management.base import BaseCommand
from donations.models import Badge

BADGES_DATA = [
    {"name": "First Donation", "description": "Made their very first food donation.", "threshold_kg": 1},
    {"name": "Bronze Donor", "description": "Donated 50kg or more of food in total.", "threshold_kg": 50},
    {"name": "Silver Donor", "description": "Donated 150kg or more of food in total.", "threshold_kg": 150},
    {"name": "Gold Donor", "description": "Donated 300kg or more of food in total.", "threshold_kg": 300},
    {"name": "Platinum Donor", "description": "Donated 500kg or more of food in total.", "threshold_kg": 500},
]


class Command(BaseCommand):
    help = "Seed donor Badge definitions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing badges before creating new ones",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            deleted_count, _ = Badge.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing badges"))

        created, skipped = 0, 0

        for data in BADGES_DATA:
            badge, was_created = Badge.objects.get_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "threshold_kg": data["threshold_kg"],
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created badge: {badge.name} ({badge.threshold_kg}kg)"))
            else:
                skipped += 1
                self.stdout.write(self.style.WARNING(f"Skipping {badge.name} (already exists)"))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created {created}, skipped {skipped}."))