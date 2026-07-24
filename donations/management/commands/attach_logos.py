#Attaches logo image files (sitting in your Downloads folder) to the
#matching Restaurant record, based on an explicit filename mapping below.

#IMPORTANT: Fill in LOGO_MAP with the ACTUAL filenames as they appear in
#your Downloads folder (check spelling/case carefully — Windows usually
#doesn't care about case, but it's good practice to match exactly).

#Usage:
   # python manage.py attach_logos
  #  python manage.py attach_logos --dry-run    # preview without saving


import os

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from donations.models import Restaurant

# Dedicated folder for logos, kept separate from your messy Downloads folder.
# Move your 10 renamed logo files here before running this command.
SOURCE_DIR = r"C:\Users\admin\OneDrive\Documents\Desktop\fod rescue\food-rescue\logos_to_import"

# Map: restaurant's linked username -> exact filename in SOURCE_DIR
# Fill these in to match your real downloaded files.
LOGO_MAP = {
    "resto_freshbites":     "freshbites.png",
    "resto_spicetrail":     "spice trail.png",
    "resto_tandoortales":   "tandoor tales.png",
    "resto_greengrove":     "green grove.png",
    "resto_wokthisway":     "wok this way.png",
    "resto_streetsizzle":   "street sizzle.png",
    "resto_butterandbread": "butter and bread co.png",
    "resto_gharcachav":     "ghar cha chav.png",
    "resto_dosadiaries":    "dosa diaries.png",
    "resto_flavorfable":    "flavour fabel.png",
}


class Command(BaseCommand):
    help = "Attach downloaded logo images to matching restaurants by username."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would happen without actually saving anything.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if not os.path.isdir(SOURCE_DIR):
            raise CommandError(f"SOURCE_DIR does not exist: {SOURCE_DIR}")

        attached, missing_file, missing_restaurant = 0, [], []

        for username, filename in LOGO_MAP.items():
            filepath = os.path.join(SOURCE_DIR, filename)

            restaurant = Restaurant.objects.filter(user__username=username).first()
            if not restaurant:
                missing_restaurant.append(username)
                continue

            if not os.path.isfile(filepath):
                missing_file.append(filename)
                continue

            if dry_run:
                self.stdout.write(f"[dry-run] Would attach '{filename}' -> {restaurant.name}")
                continue

            with open(filepath, "rb") as f:
                restaurant.logo.save(filename, File(f), save=True)

            attached += 1
            self.stdout.write(self.style.SUCCESS(f"Attached '{filename}' -> {restaurant.name}"))

        if missing_restaurant:
            self.stdout.write(self.style.WARNING(
                f"\nNo restaurant found for usernames: {missing_restaurant}"
            ))
        if missing_file:
            self.stdout.write(self.style.WARNING(
                f"Files not found in {SOURCE_DIR}: {missing_file}"
            ))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"\nDone. Attached {attached} logo(s)."))