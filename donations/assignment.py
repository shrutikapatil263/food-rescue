"""
Auto-assignment logic for Donations.

Place this file at:  yourapp/assignment.py
(sibling to matching.py and models.py)

Depends on matching.get_available_agents_for_donation (already in matching.py).

Usage:
    from donations.assignment import assign_nearest_agent

    result = assign_nearest_agent(donation)
    if result.success:
        print(f"Assigned {result.agent.name}, {result.distance_km} km away")
    else:
        print(result.reason)
"""

from dataclasses import dataclass
from typing import Optional

from django.db import transaction
from django.utils import timezone

from donations.matching import get_available_agents_for_donation
from donations.models import AssignmentLog, Agent, Donation
from donations.notifications import notify_donation_assigned, notify_status_change


@dataclass
class AssignmentResult:
    success: bool
    agent: Optional[Agent] = None
    distance_km: Optional[float] = None
    reason: str = ""


def assign_nearest_agent(donation: Donation) -> AssignmentResult:
    """
    Finds the nearest available, verified agent for this donation's restaurant
    and assigns them. Refuses to reassign a donation that's already assigned/
    picked_up/delivered — use reassign_agent() explicitly for that case.
    """
    if donation.status not in ('pending', 'expired'):
        return AssignmentResult(
            success=False,
            reason=f"Donation status is '{donation.status}', not eligible for assignment.",
        )

    matches = get_available_agents_for_donation(donation)
    if not matches:
        return AssignmentResult(success=False, reason="No available agents in range.")

    nearest_agent, distance_km = matches[0]

    with transaction.atomic():
        # Lock the rows we're about to mutate so two donations can't grab
        # the same agent in a race between two near-simultaneous requests.
        agent = Agent.objects.select_for_update().get(pk=nearest_agent.pk)
        donation = Donation.objects.select_for_update().get(pk=donation.pk)

        if agent.availability_status != 'available':
            # Someone else grabbed this agent between the match query and now.
            return AssignmentResult(success=False, reason="Agent was taken by another assignment.")

        if donation.status not in ('pending', 'expired'):
            return AssignmentResult(success=False, reason="Donation was already assigned elsewhere.")

        was_reassignment = donation.status == 'expired'

        donation.assigned_agent = agent
        donation.assigned_at = timezone.now()
        donation.status = 'assigned'
        donation.save(update_fields=['assigned_agent', 'assigned_at', 'status', 'updated_at'])

        agent.availability_status = 'on_pickup'
        agent.save(update_fields=['availability_status', 'updated_at'])

        AssignmentLog.objects.create(
            donation=donation,
            agent=agent,
            action='reassigned' if was_reassignment else 'assigned',
            notes=f"Auto-assigned, {distance_km} km away.",
        )

    notify_donation_assigned(donation, distance_km)
    return AssignmentResult(success=True, agent=agent, distance_km=distance_km)


def release_agent(donation: Donation, action: str, notes: str = ""):
    """
    Call when a donation's assignment ends (picked_up/delivered/cancelled/expired)
    so the agent becomes available again and the event is logged.
    """
    if action not in dict(AssignmentLog.ACTION_CHOICES):
        raise ValueError(f"Unknown action '{action}'")

    with transaction.atomic():
        agent = donation.assigned_agent
        if agent:
            agent = Agent.objects.select_for_update().get(pk=agent.pk)
            agent.availability_status = 'available'
            agent.save(update_fields=['availability_status', 'updated_at'])

        AssignmentLog.objects.create(
            donation=donation,
            agent=agent,
            action=action,
            notes=notes,
        )

    notify_status_change(donation, action)
