"""
Place at: donations/notifications.py
(sibling to matching.py, assignment.py, models.py)

Sends email notifications when a donation is assigned, picked up,
delivered, cancelled, or expired. SMS is stubbed out at the bottom —
disabled by default since it needs a paid Twilio account.
"""

import logging

from django.core.mail import send_mail

from donations.models import Donation

logger = logging.getLogger(__name__)


def notify_donation_assigned(donation: Donation, distance_km: float = None):
    """Notify both the restaurant and the agent that a match was made."""
    agent = donation.assigned_agent
    restaurant = donation.restaurant

    if not agent:
        return

    distance_note = f" ({distance_km} km away)" if distance_km is not None else ""

    # --- Email to the agent ---
    _safe_send_mail(
        subject=f"New pickup assigned: {donation.food_name}",
        message=(
            f"Hi {agent.name},\n\n"
            f"You've been assigned a new pickup{distance_note}.\n\n"
            f"Restaurant: {restaurant.name}\n"
            f"Address: {donation.pickup_address}\n"
            f"Food: {donation.food_name} ({donation.quantity_kg} kg, "
            f"~{donation.estimated_servings} servings)\n"
            f"Pickup deadline: {donation.pickup_deadline.strftime('%d %b %Y, %I:%M %p')}\n\n"
            f"Please head over before the deadline.\n"
        ),
        recipient_email=agent.email,
    )

    # --- Email to the restaurant ---
    _safe_send_mail(
        subject=f"Agent assigned for your donation: {donation.food_name}",
        message=(
            f"Hi {restaurant.owner_name},\n\n"
            f"{agent.name} has been assigned to pick up your donation "
            f"'{donation.food_name}'{distance_note}.\n"
            f"Agent contact: {agent.phone_number}\n\n"
            f"Thank you for your donation!\n"
        ),
        recipient_email=restaurant.email,
    )


def notify_status_change(donation: Donation, new_status: str):
    """Notify the restaurant (and agent, where relevant) of a status update."""
    restaurant = donation.restaurant
    agent = donation.assigned_agent

    status_messages = {
        'picked_up': f"Your donation '{donation.food_name}' has been picked up.",
        'delivered': f"Your donation '{donation.food_name}' has been delivered successfully. Thank you!",
        'cancelled': f"Your donation '{donation.food_name}' was cancelled.",
        'expired': f"Your donation '{donation.food_name}' expired before pickup and needs reassignment.",
    }

    message = status_messages.get(new_status)
    if not message:
        return

    _safe_send_mail(
        subject=f"Donation update: {donation.food_name} — {new_status}",
        message=f"Hi {restaurant.owner_name},\n\n{message}\n",
        recipient_email=restaurant.email,
    )

    if agent and new_status == 'delivered':
        _safe_send_mail(
            subject="Delivery confirmed — thank you!",
            message=f"Hi {agent.name},\n\nYour delivery of '{donation.food_name}' was marked complete. Thanks for your help!\n",
            recipient_email=agent.email,
        )


def _safe_send_mail(subject, message, recipient_email):
    """
    Wraps send_mail so a notification failure (bad email, SMTP down, etc.)
    never breaks the actual assignment/status-update transaction.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,  # uses DEFAULT_FROM_EMAIL
            recipient_list=[recipient_email],
            fail_silently=False,
        )
    except Exception as exc:
        logger.warning(f"Failed to send notification email to {recipient_email}: {exc}")


# ---------------------------------------------------------------------------
# OPTIONAL: SMS via Twilio — disabled by default.
#
# To enable:
#   1. pip install twilio
#   2. Sign up at twilio.com, get an Account SID, Auth Token, and a phone number
#      (paid service; has a free trial with limited credits)
#   3. Add to settings.py:
#        TWILIO_ACCOUNT_SID = "..."
#        TWILIO_AUTH_TOKEN = "..."
#        TWILIO_FROM_NUMBER = "+1..."
#   4. Uncomment the function below and call it alongside the email calls above.
# ---------------------------------------------------------------------------

# from django.conf import settings
# from twilio.rest import Client
#
# def send_sms(to_number: str, body: str):
#     try:
#         client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
#         client.messages.create(body=body, from_=settings.TWILIO_FROM_NUMBER, to=to_number)
#     except Exception as exc:
#         logger.warning(f"Failed to send SMS to {to_number}: {exc}"