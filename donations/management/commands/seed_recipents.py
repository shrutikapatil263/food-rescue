import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from donations.models import Recipient

# Ichalkaranji, Maharashtra area — realistic-ish lat/long spread for local testing
BASE_LAT, BASE_LNG = 16.6910, 74.4602

# NOTE: names are chosen to sound warm/trustworthy — the kind of name that
# makes a restaurant feel confident their donated food is going somewhere good.
RECIPIENTS_DATA = [
    {"username": "recipient_ashakiran", "name": "Asha Kiran Bal Ashram", "type": "orphanage", "contact": "Sunita More", "phone": "9876700001", "email": "ashakiran@example.com", "address": "Near Bus Stand, Ichalkaranji", "capacity": 60, "verification": "verified"},
    {"username": "recipient_sevasadan", "name": "Seva Sadan Old Age Home", "type": "old_age_home", "contact": "Anand Joshi", "phone": "9876700002", "email": "sevasadan@example.com", "address": "MIDC Road, Ichalkaranji", "capacity": 40, "verification": "verified"},
    {"username": "recipient_annapoorna", "name": "Annapoorna Community Kitchen", "type": "community_kitchen", "contact": "Meera Nair", "phone": "9876700003", "email": "annapoorna@example.com", "address": "Rajarampuri, Kolhapur", "capacity": 100, "verification": "pending"},
    {"username": "recipient_umeedngo", "name": "Umeed Foundation NGO", "type": "ngo", "contact": "Farhan Sheikh", "phone": "9876700004", "email": "umeedngo@example.com", "address": "Shahupuri, Kolhapur", "capacity": 80, "verification": "verified"},
    {"username": "recipient_snehchhaya", "name": "Sneh Chhaya Shelter", "type": "shelter", "contact": "Kavita Salunkhe", "phone": "9876700005", "email": "snehchhaya@example.com", "address": "Rukdi Road, Ichalkaranji", "capacity": 50, "verification": "verified"},
    {"username": "recipient_balvikas", "name": "Bal Vikas Orphanage", "type": "orphanage", "contact": "Prakash Chougule", "phone": "9876700006", "email": "balvikas@example.com", "address": "Tarabai Park, Kolhapur", "capacity": 45, "verification": "unverified"},
    {"username": "recipient_matoshriwadi", "name": "Matoshri Old Age Home", "type": "old_age_home", "contact": "Vandana Pawar", "phone": "9876700007", "email": "matoshriwadi@example.com", "address": "Jawahar Nagar, Ichalkaranji", "capacity": 35, "verification": "verified"},
    {"username": "recipient_prasadamseva", "name": "Prasadam Seva Trust", "type": "community_kitchen", "contact": "Ganesh Koli", "phone": "9876700008", "email": "prasadamseva@example.com", "address": "Station Road, Ichalkaranji", "capacity": 120, "verification": "verified"},
    {"username": "recipient_aashray", "name": "Aashray Foundation", "type": "ngo", "contact": "Neha Kapoor", "phone": "9876700009", "email": "aashray@example.com", "address": "College Road, Kolhapur", "capacity": 70, "verification": "pending"},
    {"username": "recipient_mayasadan", "name": "Maya Sadan Shelter Home", "type": "shelter", "contact": "Rohit Deshmukh", "phone": "9876700010", "email": "mayasadan@example.com", "address": "Shivaji Chowk, Ichalkaranji", "capacity": 55, "verification": "verified"},
]

DEFAULT_PASSWORD = "RecipientPass123!"  # change/reset after testing


class Command(BaseCommand):
    help = "Seed 10 test Recipient records with linked User accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seeded recipients/users before creating new ones",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            usernames = [r["username"] for r in RECIPIENTS_DATA]
            deleted_count, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing seeded records"))

        created_count = 0
        skipped_count = 0

        for data in RECIPIENTS_DATA:
            if User.objects.filter(username=data["username"]).exists():
                self.stdout.write(self.style.WARNING(f"Skipping {data['username']} (already exists)"))
                skipped_count += 1
                continue

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=DEFAULT_PASSWORD,
                first_name=data["contact"].split()[0],
                last_name=data["contact"].split()[-1],
            )

            Recipient.objects.create(
                user=user,
                name=data["name"],
                recipient_type=data["type"],
                contact_person=data["contact"],
                phone_number=data["phone"],
                email=data["email"],
                address=data["address"],
                latitude=round(BASE_LAT + random.uniform(-0.03, 0.03), 6),
                longitude=round(BASE_LNG + random.uniform(-0.03, 0.03), 6),
                capacity_people=data["capacity"],
                verification_status=data["verification"],
                is_active=True,
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created recipient: {data['name']} ({data['username']})"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created {created_count}, skipped {skipped_count}."
        ))
        self.stdout.write(f"All seeded users share the password: {DEFAULT_PASSWORD}")