"""
Place at: donations/management/commands/expire_overdue_donations.py

Finds donations whose pickup_deadline has passed but are still stuck in
'pending' or 'assigned', and flips them to 'expired' — freeing the agent
(if one was assigned) and sending the notification email.

Usage:
    python manage.py expire_overdue_donations
    python manage.py expire_overdue_donations --dry-run

To run this automatically instead of by hand, schedule it with Windows
Task Scheduler (or cron on Linux/Mac) to run every 15-30 minutes, e.g.:
    python manage.py expire_overdue_donations
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from donations.assignment import release_agent
from donations.models import AssignmentLog, Donation
from donations.notifications import notify_status_change


class Command(BaseCommand):
    help = "Expire donations whose pickup_deadline has passed but are still pending/assigned."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        now = timezone.now()

        overdue = Donation.objects.filter(
            status__in=["pending", "assigned"],
            pickup_deadline__lt=now,
        )

        if not overdue.exists():
            self.stdout.write("No overdue donations found. Everything's on track.")
            return

        count = 0
        for donation in overdue:
            if dry_run:
                self.stdout.write(
                    f"[dry-run] Would expire #{donation.id} '{donation.food_name}' "
                    f"(status={donation.status}, deadline was {donation.pickup_deadline})"
                )
                continue

            had_agent = donation.assigned_agent is not None

            donation.status = 'expired'
            donation.save(update_fields=['status', 'updated_at'])

            if had_agent:
                # Frees the agent, logs the event, and sends the notification —
                # release_agent() already does all of this.
                release_agent(donation, action='expired', notes='Auto-expired: past pickup deadline.')
            else:
                # No agent was ever assigned — still log and notify.
                AssignmentLog.objects.create(
                    donation=donation,
                    agent=None,
                    action='expired',
                    notes='Auto-expired: past pickup deadline, no agent had been assigned.',
                )
                notify_status_change(donation, 'expired')

            count += 1
            self.stdout.write(self.style.WARNING(
                f"Expired #{donation.id} '{donation.food_name}'"
            ))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(f"\nDone. Expired {count} donation(s)."))