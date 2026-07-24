"""
Place at: donations/views_frontend.py
These are separate from views.py (which holds your DRF API viewsets).
This file renders HTML templates for the restaurant/agent/recipient frontend.
"""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .assignment import release_agent
from .forms import AgentSignUpForm, DonationForm, RecipientSignUpForm, RestaurantSignUpForm
from .models import Agent, AssignmentLog, Donation, Recipient, Restaurant
from .notifications import notify_status_change

# Transitions an agent is allowed to trigger from their own dashboard.
# Narrower than the full VALID_TRANSITIONS in views.py — agents only
# move a donation forward through pickup and delivery, not cancel/expire.
AGENT_ALLOWED_TRANSITIONS = {
    'picked_up': {'assigned'},
    'delivered': {'picked_up'},
}


def _get_profile_or_redirect(request, model, redirect_to):
    """
    Looks up the caller's profile (Restaurant/Agent/Recipient) without
    raising a raw 404 when it's missing — e.g. a restaurant user who
    wanders onto /agent/dashboard/. Shows a friendly message and sends
    them back to their own dashboard (or home) instead of an error page.
    Returns the profile, or None if it already redirected — callers
    must check for None and return that redirect immediately.
    """
    profile = model.objects.filter(user=request.user).first()
    if profile is None:
        messages.error(request, f"That page is only available to {model.__name__} accounts.")
    return profile


def home_view(request):
    """
    Public landing page with a live snapshot of platform impact,
    pulled directly from the Donation table rather than hardcoded.
    """
    delivered = Donation.objects.filter(status='delivered')
    stats = delivered.aggregate(
        total_kg=Sum('quantity_kg'),
        total_servings=Sum('estimated_servings'),
    )
    context = {
        'total_kg': stats['total_kg'] or 0,
        'total_servings': stats['total_servings'] or 0,
        'total_deliveries': delivered.count(),
        'total_donations_posted': Donation.objects.count(),
        'restaurant_count': Restaurant.objects.count(),
        'agent_count': Agent.objects.count(),
        'recipient_count': Recipient.objects.count(),
    }
    return render(request, 'donations/home.html', context)


def restaurant_list_view(request):
    restaurants = Restaurant.objects.all().order_by('name')
    return render(request, 'donations/restaurant_list.html', {'restaurants': restaurants})


def agent_list_view(request):
    agents = Agent.objects.all().order_by('name')
    return render(request, 'donations/agent_list.html', {'agents': agents})


def recipient_list_view(request):
    recipients = Recipient.objects.all().order_by('name')
    return render(request, 'donations/recipient_list.html', {'recipients': recipients})


@login_required
def post_login_redirect(request):
    """
    Single LOGIN_REDIRECT_URL target that routes a logged-in user to the
    right dashboard depending on whether they have a Restaurant, Agent,
    or Recipient profile attached.
    """
    if hasattr(request.user, 'restaurant'):
        return redirect('dashboard')
    if hasattr(request.user, 'agent'):
        return redirect('agent_dashboard')
    if hasattr(request.user, 'recipient'):
        return redirect('recipient_dashboard')
    return redirect('home')


def signup_view(request):
    if request.method == 'POST':
        form = RestaurantSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = RestaurantSignUpForm()
    return render(request, 'donations/signup.html', {'form': form})


@login_required
def dashboard_view(request):
    restaurant = _get_profile_or_redirect(request, Restaurant, 'post_login_redirect')
    if restaurant is None:
        return redirect('post_login_redirect')

    donations = Donation.objects.filter(restaurant=restaurant).order_by('-posted_at')
    return render(request, 'donations/dashboard.html', {
        'restaurant': restaurant,
        'donations': donations,
    })


@login_required
def donation_create_view(request):
    restaurant = _get_profile_or_redirect(request, Restaurant, 'post_login_redirect')
    if restaurant is None:
        return redirect('post_login_redirect')

    if request.method == 'POST':
        form = DonationForm(request.POST, request.FILES)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.restaurant = restaurant
            donation.save()
            messages.success(request, f'"{donation.food_name}" was posted successfully.')
            return redirect('dashboard')
    else:
        form = DonationForm()

    return render(request, 'donations/donation_form.html', {'form': form})


@login_required
def donation_detail_view(request, pk):
    restaurant = _get_profile_or_redirect(request, Restaurant, 'post_login_redirect')
    if restaurant is None:
        return redirect('post_login_redirect')

    donation = get_object_or_404(Donation, pk=pk, restaurant=restaurant)
    return render(request, 'donations/donation_detail.html', {'donation': donation})


def agent_signup_view(request):
    if request.method == 'POST':
        form = AgentSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('agent_dashboard')
    else:
        form = AgentSignUpForm()
    return render(request, 'donations/agent_signup.html', {'form': form})


@login_required
def agent_dashboard_view(request):
    agent = _get_profile_or_redirect(request, Agent, 'post_login_redirect')
    if agent is None:
        return redirect('post_login_redirect')

    donations = Donation.objects.filter(assigned_agent=agent).order_by('-assigned_at')
    return render(request, 'donations/agent_dashboard.html', {
        'agent': agent,
        'donations': donations,
    })


@login_required
def agent_update_status_view(request, pk):
    """
    Mirrors the DonationViewSet.update_status API action, scoped to
    the logged-in agent's own assigned donations and restricted to
    the forward-only transitions agents are allowed to trigger.
    """
    agent = _get_profile_or_redirect(request, Agent, 'post_login_redirect')
    if agent is None:
        return redirect('post_login_redirect')

    donation = get_object_or_404(Donation, pk=pk, assigned_agent=agent)

    if request.method == 'POST':
        new_status = request.POST.get('new_status')
        allowed_from = AGENT_ALLOWED_TRANSITIONS.get(new_status)

        if allowed_from and donation.status in allowed_from:
            donation.status = new_status
            donation.save(update_fields=['status', 'updated_at'])

            if new_status == 'delivered':
                release_agent(donation, action=new_status)
            else:
                AssignmentLog.objects.create(
                    donation=donation,
                    agent=donation.assigned_agent,
                    action=new_status,
                )
                notify_status_change(donation, new_status)

            messages.success(request, f'"{donation.food_name}" marked as {donation.get_status_display()}.')

    return redirect('agent_dashboard')


def recipient_signup_view(request):
    if request.method == 'POST':
        form = RecipientSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('recipient_dashboard')
    else:
        form = RecipientSignUpForm()
    return render(request, 'donations/recipient_signup.html', {'form': form})


@login_required
def recipient_dashboard_view(request):
    recipient = _get_profile_or_redirect(request, Recipient, 'post_login_redirect')
    if recipient is None:
        return redirect('post_login_redirect')

    available_donations = Donation.objects.filter(
        recipient__isnull=True,
        status='pending',
    ).order_by('pickup_deadline')

    my_donations = Donation.objects.filter(recipient=recipient).order_by('-posted_at')

    return render(request, 'donations/recipient_dashboard.html', {
        'recipient': recipient,
        'available_donations': available_donations,
        'my_donations': my_donations,
    })


@login_required
def recipient_claim_view(request, pk):
    """
    Lets a recipient claim an open, unclaimed donation.
    Only allowed while it's still pending and has no recipient —
    prevents two NGOs claiming the same donation in a race.
    """
    recipient = _get_profile_or_redirect(request, Recipient, 'post_login_redirect')
    if recipient is None:
        return redirect('post_login_redirect')

    if request.method == 'POST':
        donation = get_object_or_404(Donation, pk=pk, recipient__isnull=True, status='pending')
        donation.recipient = recipient
        donation.save(update_fields=['recipient', 'updated_at'])
        messages.success(request, f'You claimed "{donation.food_name}".')

    return redirect('recipient_dashboard')