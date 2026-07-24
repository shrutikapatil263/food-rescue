import random
from datetime import time

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from donations.models import Restaurant

# Ichalkaranji, Maharashtra area — realistic-ish lat/long spread for local testing
BASE_LAT, BASE_LNG = 16.6910, 74.4602

# NOTE: names are chosen to sound appetizing/inviting — the kind of name that
# makes someone want to actually go taste the food, not just a generic label.
RESTAURANTS_DATA = [
    {"username": "resto_freshbites", "name": "FreshBites", "owner": "Ramesh Patil", "phone": "9876600001", "email": "freshbites@example.com", "address": "Shivaji Chowk, Ichalkaranji", "cuisine": "fast_food", "open": time(9, 0), "close": time(23, 0)},
    {"username": "resto_spicetrail", "name": "Spice Trail", "owner": "Lakshmi Iyer", "phone": "9876600002", "email": "spicetrail@example.com", "address": "College Road, Kolhapur", "cuisine": "south_indian", "open": time(7, 30), "close": time(22, 0)},
    {"username": "resto_tandoortales", "name": "Tandoor Tales", "owner": "Gurpreet Singh", "phone": "9876600003", "email": "tandoortales@example.com", "address": "Station Road, Ichalkaranji", "cuisine": "north_indian", "open": time(11, 0), "close": time(23, 30)},
    {"username": "resto_greengrove", "name": "Green Grove Kitchen", "owner": "Suresh Kulkarni", "phone": "9876600004", "email": "greengrove@example.com", "address": "MIDC Road, Ichalkaranji", "cuisine": "vegetarian", "open": time(8, 0), "close": time(21, 30)},
    {"username": "resto_wokthisway", "name": "Wok This Way", "owner": "Chen Wei Liu", "phone": "9876600005", "email": "wokthisway@example.com", "address": "Rajarampuri, Kolhapur", "cuisine": "chinese", "open": time(12, 0), "close": time(23, 0)},
    {"username": "resto_streetsizzle", "name": "Street Sizzle", "owner": "Amit Yadav", "phone": "9876600006", "email": "streetsizzle@example.com", "address": "Bus Stand Road, Ichalkaranji", "cuisine": "street_food", "open": time(16, 0), "close": time(23, 45)},
    {"username": "resto_butterandbread", "name": "Butter & Bread Co.", "owner": "Neha Kapoor", "phone": "9876600007", "email": "butterandbread@example.com", "address": "Shahupuri, Kolhapur", "cuisine": "continental", "open": time(10, 0), "close": time(22, 30)},
    {"username": "resto_gharcachav", "name": "Ghar Cha Chav", "owner": "Sunita More", "phone": "9876600008", "email": "gharchachav@example.com", "address": "Rukdi Road, Ichalkaranji", "cuisine": "north_indian", "open": time(8, 30), "close": time(21, 0)},
    {"username": "resto_dosadiaries", "name": "Dosa Diaries", "owner": "Meera Nair", "phone": "9876600009", "email": "dosadiaries@example.com", "address": "Tarabai Park, Kolhapur", "cuisine": "south_indian", "open": time(7, 0), "close": time(20, 30)},
    {"username": "resto_flavorfable", "name": "Flavor Fable", "owner": "Rohit Deshmukh", "phone": "9876600010", "email": "flavorfable@example.com", "address": "Jawahar Nagar, Ichalkaranji", "cuisine": "other", "open": time(9, 30), "close": time(22, 15)},
]

DEFAULT_PASSWORD = "RestoPass123!"  # change/reset after testing


class Command(BaseCommand):
    help = "Seed 10 test Restaurant records with linked User accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seeded restaurants/users before creating new ones",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            usernames = [r["username"] for r in RESTAURANTS_DATA]
            deleted_count, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing seeded records"))

        created_count = 0
        skipped_count = 0

        for data in RESTAURANTS_DATA:
            if User.objects.filter(username=data["username"]).exists():
                self.stdout.write(self.style.WARNING(f"Skipping {data['username']} (already exists)"))
                skipped_count += 1
                continue

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=DEFAULT_PASSWORD,
                first_name=data["owner"].split()[0],
                last_name=data["owner"].split()[-1],
            )

            Restaurant.objects.create(
                user=user,
                name=data["name"],
                owner_name=data["owner"],
                email=data["email"],
                phone_number=data["phone"],
                address=data["address"],
                latitude=round(BASE_LAT + random.uniform(-0.03, 0.03), 6),
                longitude=round(BASE_LNG + random.uniform(-0.03, 0.03), 6),
                cuisine_type=data["cuisine"],
                opening_time=data["open"],
                closing_time=data["close"],
                verification_status="verified",
                is_active=True,
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created restaurant: {data['name']} ({data['username']})"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created {created_count}, skipped {skipped_count}."
        ))
        self.stdout.write(f"All seeded users share the password: {DEFAULT_PASSWORD}")