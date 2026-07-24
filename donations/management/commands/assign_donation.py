"""
Place at: yourapp/management/commands/assign_donation.py

Usage:
    python manage.py assign_donation <donation_id>
"""

from django.core.management.base import BaseCommand, CommandError

from donations.assignment import assign_nearest_agent
from donations.models import Donation


class Command(BaseCommand):
    help = "Attempt to auto-assign the nearest available agent to a donation."

    def add_arguments(self, parser):
        parser.add_argument("donation_id", type=int)

    def handle(self, *args, **options):
        try:
            donation = Donation.objects.get(pk=options["donation_id"])
        except Donation.DoesNotExist:
            raise CommandError(f"No donation with id {options['donation_id']}")

        result = assign_nearest_agent(donation)

        if result.success:
            self.stdout.write(self.style.SUCCESS(
                f"Assigned '{result.agent.name}' to donation #{donation.id} "
                f"({result.distance_km} km away)."
            ))
        else:
            self.stdout.write(self.style.WARNING(f"Could not assign: {result.reason}"))