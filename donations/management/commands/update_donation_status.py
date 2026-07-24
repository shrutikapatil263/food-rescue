"""
Place at: donations/management/commands/update_donation_status.py

Usage:
    python manage.py update_donation_status <donation_id> picked_up
    python manage.py update_donation_status <donation_id> delivered
    python manage.py update_donation_status <donation_id> cancelled
"""

from django.core.management.base import BaseCommand, CommandError

from donations.assignment import release_agent
from donations.models import Donation

# Which current statuses are allowed to move to which next status
VALID_TRANSITIONS = {
    'picked_up': {'assigned'},
    'delivered': {'picked_up'},
    'cancelled': {'pending', 'assigned', 'picked_up'},
    'expired': {'assigned'},
}


class Command(BaseCommand):
    help = "Move a donation to picked_up / delivered / cancelled / expired, releasing the agent as needed."

    def add_arguments(self, parser):
        parser.add_argument("donation_id", type=int)
        parser.add_argument("new_status", choices=list(VALID_TRANSITIONS.keys()))

    def handle(self, *args, **options):
        try:
            donation = Donation.objects.get(pk=options["donation_id"])
        except Donation.DoesNotExist:
            raise CommandError(f"No donation with id {options['donation_id']}")

        new_status = options["new_status"]
        allowed_from = VALID_TRANSITIONS[new_status]

        if donation.status not in allowed_from:
            raise CommandError(
                f"Cannot move donation from '{donation.status}' to '{new_status}'. "
                f"Allowed only from: {sorted(allowed_from)}"
            )

        donation.status = new_status
        donation.save(update_fields=['status', 'updated_at'])

        # picked_up doesn't free the agent (they're still out on the delivery),
        # but it should still be logged; delivered/cancelled/expired both log
        # AND free the agent back to 'available'.
        if new_status in ('delivered', 'cancelled', 'expired'):
            release_agent(donation, action=new_status)
            agent_name = donation.assigned_agent.name if donation.assigned_agent else "(no agent)"
            self.stdout.write(self.style.SUCCESS(
                f"Donation #{donation.id} -> {new_status}. Released agent: {agent_name}"
            ))
        else:
            from donations.models import AssignmentLog
            AssignmentLog.objects.create(
                donation=donation,
                agent=donation.assigned_agent,
                action=new_status,
            )
            self.stdout.write(self.style.SUCCESS(
                f"Donation #{donation.id} -> {new_status}."
            ))