#Usage:
 #   python manage.py find_nearby_agents --restaurant resto_freshbites
  #  python manage.py find_nearby_agents --recipient recipient_ashakiran


from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from donations.matching import (
    get_available_agents_for_restaurant,
    get_available_agents_for_recipient,
)
from donations.models import Restaurant, Recipient


class Command(BaseCommand):
    help = "Find available agents near a given restaurant or recipient (by username)."

    def add_arguments(self, parser):
        parser.add_argument("--restaurant", help="Restaurant's linked username")
        parser.add_argument("--recipient", help="Recipient's linked username")

    def handle(self, *args, **options):
        if not options["restaurant"] and not options["recipient"]:
            raise CommandError("Pass either --restaurant <username> or --recipient <username>")

        if options["restaurant"]:
            user = User.objects.filter(username=options["restaurant"]).first()
            if not user or not hasattr(user, "restaurant"):
                raise CommandError(f"No restaurant found for username '{options['restaurant']}'")
            restaurant = user.restaurant
            self.stdout.write(f"Restaurant: {restaurant.name} ({restaurant.latitude}, {restaurant.longitude})\n")
            matches = get_available_agents_for_restaurant(restaurant)
        else:
            user = User.objects.filter(username=options["recipient"]).first()
            if not user or not hasattr(user, "recipient"):
                raise CommandError(f"No recipient found for username '{options['recipient']}'")
            recipient = user.recipient
            self.stdout.write(f"Recipient: {recipient.name} ({recipient.latitude}, {recipient.longitude})\n")
            matches = get_available_agents_for_recipient(recipient)

        if not matches:
            self.stdout.write(self.style.WARNING("No available agents in range."))
            return

        self.stdout.write(self.style.SUCCESS(f"Found {len(matches)} available agent(s):"))
        for agent, distance_km in matches:
            self.stdout.write(
                f"  {agent.name:20s} distance={distance_km:>6} km  "
                f"radius={agent.service_radius_km} km  status={agent.availability_status}"
            )