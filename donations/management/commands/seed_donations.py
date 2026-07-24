"""
Management command to seed 10 test Donation records, linked to
whichever Restaurants, Agents, and Recipients already exist in your database.

REQUIRES: at least a few Restaurants and Agents already created (via admin or seed scripts).
Recipients are optional (some donations are left unassigned to a recipient, matching real flow).

USAGE:
    Place this file at: donations/management/commands/seed_donations.py

    Then run:
        python manage.py seed_donations

    To wipe and re-seed:
        python manage.py seed_donations --reset
"""

import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from donations.models import Donation, Restaurant, Agent, Recipient

# NOTE: choice values below are confirmed against your actual model:
#   status: pending, assigned, picked_up, delivered, expired
#   food_category: ASSUMED — adjust if your FOOD_CATEGORY_CHOICES differ
#   storage_condition: refrigerated, room_temperature, hot_held
#   verification_status: unverified, verified, rejected

FOOD_ITEMS = [
    ("Vegetable Biryani", "veg", 12.5, 50),
    ("Idli Sambar (bulk)", "veg", 8.0, 40),
    ("Fried Rice & Noodles", "mixed", 15.0, 60),
    ("Assorted Sandwiches", "mixed", 6.5, 30),
    ("Bread & Pastries (unsold)", "veg", 5.0, 25),
    ("Dal Rice Thali (surplus)", "veg", 10.0, 45),
    ("Dosa Batter & Chutney", "veg", 4.0, 20),
    ("Wedding Function Surplus", "mixed", 30.0, 120),
    ("Thali Combo Surplus", "veg", 9.0, 35),
    ("Unsold Pizzas", "veg", 7.0, 28),
]

STORAGE_OPTIONS = ["refrigerated", "room_temperature", "hot_held"]

# Each tuple: (status, has_agent, has_recipient, verification, hours_ago_prepared, hours_ago_deadline)
LIFECYCLE_PATTERN = [
    ("delivered", True, True, "verified", 6, 2),
    ("delivered", True, True, "verified", 5, 1),
    ("picked_up", True, True, "verified", 3, -1),
    ("assigned", True, False, "verified", 2, -3),
    ("assigned", True, False, "unverified", 1, -4),
    ("pending", False, False, "unverified", 1, -5),
    ("pending", False, False, "unverified", 0, -6),
    ("delivered", True, True, "verified", 10, 4),
    ("picked_up", True, True, "verified", 3, -1),
    ("expired", False, False, "rejected", 8, 3),
]


class Command(BaseCommand):
    help = "Seed 10 test Donation records using existing Restaurants, Agents, and Recipients"

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing donations before creating new ones",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            deleted_count, _ = Donation.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} existing donations"))

        restaurants = list(Restaurant.objects.all())
        agents = list(Agent.objects.all())
        recipients = list(Recipient.objects.all())

        if not restaurants:
            self.stdout.write(self.style.ERROR(
                "No Restaurant records found. Create/seed at least one Restaurant first."
            ))
            return

        if not agents:
            self.stdout.write(self.style.WARNING(
                "No Agent records found — donations needing an agent will be left unassigned."
            ))

        now = timezone.now()
        created = 0

        for i, (food_name, category, qty, servings) in enumerate(FOOD_ITEMS):
            status, has_agent, has_recipient, verification, hrs_prepared, hrs_deadline = LIFECYCLE_PATTERN[i]

            restaurant = random.choice(restaurants)
            agent = random.choice(agents) if (has_agent and agents) else None
            recipient = random.choice(recipients) if (has_recipient and recipients) else None

            prepared_at = now - timedelta(hours=hrs_prepared)
            pickup_deadline = now - timedelta(hours=hrs_deadline)

            donation = Donation.objects.create(
                restaurant=restaurant,
                recipient=recipient,
                food_name=food_name,
                quantity_kg=qty,
                estimated_servings=servings,
                prepared_at=prepared_at,
                pickup_deadline=pickup_deadline,
                status=status,
                assigned_agent=agent,
                assigned_at=(now - timedelta(hours=max(hrs_prepared - 1, 0))) if agent else None,
                food_category=category,
                storage_condition=random.choice(STORAGE_OPTIONS),
                verification_status=verification,
                pickup_address=f"{restaurant.name}, Ichalkaranji, Maharashtra",
                delivery_address=f"{recipient.name}, Ichalkaranji, Maharashtra" if recipient else "",
            )

            created += 1
            self.stdout.write(self.style.SUCCESS(
                f"Created donation: {donation.food_name} ({restaurant.name}) — status={donation.status}"
            ))

        self.stdout.write(self.style.SUCCESS(f"\nDone. Created {created} donations."))