import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from donations.models import Agent

# Ichalkaranji, Maharashtra area — realistic-ish lat/long spread for local testing
BASE_LAT, BASE_LNG = 16.6910, 74.4602

# NOTE: verification_status only has two valid values: 'verified' / 'unverified'
# NOTE: completed_deliveries starts at 0 for every agent (fresh signup)
AGENTS_DATA = [
    {"username": "agent_ramesh", "name": "Ramesh Patil", "phone": "9876543210", "email": "ramesh.patil@example.com", "availability": "available", "verification": "verified"},
    {"username": "agent_suresh", "name": "Suresh Kadam", "phone": "9876543211", "email": "suresh.kadam@example.com", "availability": "on_pickup", "verification": "verified"},
    {"username": "agent_anita", "name": "Anita Shinde", "phone": "9876543212", "email": "anita.shinde@example.com", "availability": "offline", "verification": "unverified"},
    {"username": "agent_vijay", "name": "Vijay More", "phone": "9876543213", "email": "vijay.more@example.com", "availability": "available", "verification": "unverified"},
    {"username": "agent_sneha", "name": "Sneha Jadhav", "phone": "9876543214", "email": "sneha.jadhav@example.com", "availability": "available", "verification": "verified"},
    {"username": "agent_prakash", "name": "Prakash Chougule", "phone": "9876543215", "email": "prakash.chougule@example.com", "availability": "on_pickup", "verification": "verified"},
    {"username": "agent_sunita", "name": "Sunita Pawar", "phone": "9876543216", "email": "sunita.pawar@example.com", "availability": "offline", "verification": "unverified"},
    {"username": "agent_ganesh", "name": "Ganesh Koli", "phone": "9876543217", "email": "ganesh.koli@example.com", "availability": "available", "verification": "verified"},
    {"username": "agent_pooja", "name": "Pooja Desai", "phone": "9876543218", "email": "pooja.desai@example.com", "availability": "offline", "verification": "unverified"},
    {"username": "agent_manoj", "name": "Manoj Bhosale", "phone": "9876543219", "email": "manoj.bhosale@example.com", "availability": "on_pickup", "verification": "verified"},
]

DEFAULT_PASSWORD = "AgentPass123!"  # change/reset after testing


class Command(BaseCommand):
    help = "Seed 10 test Agent records with linked User accounts"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing seeded agents/users before creating new ones",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            usernames = [a["username"] for a in AGENTS_DATA]
            deleted_count, _ = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing seeded records"))

        created_count = 0
        skipped_count = 0

        for data in AGENTS_DATA:
            if User.objects.filter(username=data["username"]).exists():
                self.stdout.write(self.style.WARNING(f"Skipping {data['username']} (already exists)"))
                skipped_count += 1
                continue

            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=DEFAULT_PASSWORD,
                first_name=data["name"].split()[0],
                last_name=data["name"].split()[-1],
            )

            Agent.objects.create(
                user=user,
                name=data["name"],
                phone_number=data["phone"],
                email=data["email"],
                availability_status=data["availability"],
                current_latitude=round(BASE_LAT + random.uniform(-0.03, 0.03), 6),
                current_longitude=round(BASE_LNG + random.uniform(-0.03, 0.03), 6),
                last_location_update=timezone.now(),
                service_radius_km=round(random.uniform(3.0, 8.0), 1),
                verification_status=data["verification"],
                completed_deliveries=0,
                is_active=True,
            )

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"Created agent: {data['name']} ({data['username']})"))

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Created {created_count}, skipped {skipped_count}."
        ))
        self.stdout.write(f"All seeded users share the password: {DEFAULT_PASSWORD}")
