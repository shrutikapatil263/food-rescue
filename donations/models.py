from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


# ---------------------------------------------------------------------------
# Shared choice sets (Point 3: centralized so names don't collide/confuse)
# ---------------------------------------------------------------------------

class VerificationStatus:
    """Generic pending/verified/rejected states used by multiple models."""
    PENDING = 'pending'
    VERIFIED = 'verified'
    REJECTED = 'rejected'
    CHOICES = [
        (PENDING, 'Pending review'),
        (VERIFIED, 'Verified'),
        (REJECTED, 'Rejected'),
    ]


class DonationVerificationStatus:
    """Separate from VerificationStatus because the meaning differs:
    this is an agent's food-safety check, not an identity/KYC check."""
    UNVERIFIED = 'unverified'
    VERIFIED = 'verified'
    REJECTED = 'rejected'
    CHOICES = [
        (UNVERIFIED, 'Unverified'),
        (VERIFIED, 'Verified by agent'),
        (REJECTED, 'Rejected - unsafe'),
    ]


class AgentVerificationStatus:
    UNVERIFIED = 'unverified'
    VERIFIED = 'verified'
    CHOICES = [
        (UNVERIFIED, 'Unverified'),
        (VERIFIED, 'Verified'),
    ]


CUISINE_CHOICES = [
    ('vegetarian', 'Vegetarian'),
    ('street_food', 'Street Food'),
    ('fast_food', 'Fast Food'),
    ('north_indian', 'North Indian'),
    ('south_indian', 'South Indian'),
    ('chinese', 'Chinese'),
    ('continental', 'Continental'),
    ('other', 'Other'),
]

FOOD_CATEGORY_CHOICES = [
    ('veg', 'Vegetarian'),
    ('non_veg', 'Non-Vegetarian'),
    ('mixed', 'Mixed'),
]

STORAGE_CHOICES = [
    ('refrigerated', 'Refrigerated'),
    ('room_temperature', 'Room temperature'),
    ('hot_held', 'Kept hot/warm'),
]

DONATION_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('assigned', 'Assigned to agent'),
    ('picked_up', 'Picked up'),
    ('delivered', 'Delivered'),
    ('expired', 'Expired - reassigning'),
]

AGENT_AVAILABILITY_CHOICES = [
    ('available', 'Available'),
    ('on_pickup', 'On a pickup'),
    ('offline', 'Offline'),
]


# ---------------------------------------------------------------------------
# Restaurant
# ---------------------------------------------------------------------------

class Restaurant(models.Model):
    # Point 1: link to Django auth for login/permissions
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='restaurant')

    name = models.CharField(max_length=400)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    address = models.CharField(max_length=300)

    # Point 5: index geo fields used in "nearest restaurant/agent" queries
    latitude = models.FloatField(db_index=True)
    longitude = models.FloatField(db_index=True)

    owner_name = models.CharField(max_length=100)

    verification_status = models.CharField(
        max_length=15, choices=VerificationStatus.CHOICES,
        default=VerificationStatus.PENDING, db_index=True,
    )

    date_joined = models.DateTimeField(auto_now_add=True)
    # Point 4: track modification time
    updated_at = models.DateTimeField(auto_now=True)

    total_donated_kg = models.FloatField(default=0)

    cuisine_type = models.CharField(max_length=20, choices=CUISINE_CHOICES, default='other')
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    emergency_contact = models.CharField(max_length=15, blank=True)
    logo = models.ImageField(upload_to='restaurant_logos/', null=True, blank=True)
    preferred_pickup_window = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(closing_time__gt=models.F('opening_time')),
                name='restaurant_closing_after_opening',
            ),
        ]

    def clean(self):
        # Point 8: model-level validation (form/serializer path)
        if self.opening_time and self.closing_time and self.closing_time <= self.opening_time:
            raise ValidationError('closing_time must be after opening_time.')

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Recipient / Beneficiary  (the missing piece — who the food goes to)
# ---------------------------------------------------------------------------

class Recipient(models.Model):
    RECIPIENT_TYPE_CHOICES = [
        ('ngo', 'NGO'),
        ('shelter', 'Shelter'),
        ('orphanage', 'Orphanage'),
        ('old_age_home', 'Old age home'),
        ('community_kitchen', 'Community kitchen'),
        ('other', 'Other'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='recipient', null=True, blank=True
    )

    name = models.CharField(max_length=300)
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPE_CHOICES, default='other')
    contact_person = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    address = models.CharField(max_length=300)
    latitude = models.FloatField(db_index=True)
    longitude = models.FloatField(db_index=True)

    capacity_people = models.PositiveIntegerField(
        help_text='Approx. number of people this recipient can serve per delivery.'
    )

    verification_status = models.CharField(
        max_length=15, choices=VerificationStatus.CHOICES,
        default=VerificationStatus.PENDING, db_index=True,
    )

    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class Agent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='agent')

    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    availability_status = models.CharField(
        max_length=15, choices=AGENT_AVAILABILITY_CHOICES,
        default='offline', db_index=True,
    )

    current_latitude = models.FloatField(null=True, blank=True, db_index=True)
    current_longitude = models.FloatField(null=True, blank=True, db_index=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    service_radius_km = models.FloatField(default=5.0)

    verification_status = models.CharField(
        max_length=15, choices=AgentVerificationStatus.CHOICES,
        default=AgentVerificationStatus.UNVERIFIED, db_index=True,
    )

    # Point 2: this running total lives on Agent, not on Donation
    completed_deliveries = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    date_joined = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Donation
# ---------------------------------------------------------------------------

class Donation(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='donations')

    # The missing FK: who this food is ultimately delivered to
    recipient = models.ForeignKey(
        Recipient, on_delete=models.SET_NULL, null=True, blank=True, related_name='donations'
    )

    food_name = models.CharField(max_length=200)
    quantity_kg = models.FloatField()
    estimated_servings = models.PositiveIntegerField()

    posted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)  # Point 4

    prepared_at = models.DateTimeField()
    pickup_deadline = models.DateTimeField()

    status = models.CharField(
        max_length=20, choices=DONATION_STATUS_CHOICES, default='pending', db_index=True
    )

    assigned_agent = models.ForeignKey(
        Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_donations'
    )
    assigned_at = models.DateTimeField(null=True, blank=True)

    food_category = models.CharField(max_length=10, choices=FOOD_CATEGORY_CHOICES)
    storage_condition = models.CharField(max_length=20, choices=STORAGE_CHOICES, default='room_temperature')

    verification_status = models.CharField(
        max_length=15, choices=DonationVerificationStatus.CHOICES,
        default=DonationVerificationStatus.UNVERIFIED, db_index=True,
    )

    # Point 2: removed the confusing `total_donations` counter that lived here —
    # that kind of aggregate belongs on Restaurant/Agent, not on a single donation row.

    food_image = models.ImageField(upload_to='donation_images/', null=True, blank=True)

    pickup_address = models.CharField(max_length=300)
    delivery_address = models.CharField(max_length=300, blank=True)

    class Meta:
        # Point 5: composite index for common "pending donations near X" queries
        indexes = [
            models.Index(fields=['status', 'pickup_deadline']),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(pickup_deadline__gt=models.F('prepared_at')),
                name='donation_deadline_after_prepared',
            ),
            models.CheckConstraint(
                condition=models.Q(quantity_kg__gt=0),
                name='donation_quantity_positive',
            ),
        ]

    def clean(self):
        # Point 8: model-level validation (form/serializer path)
        if self.pickup_deadline and self.prepared_at and self.pickup_deadline <= self.prepared_at:
            raise ValidationError('pickup_deadline must be after prepared_at.')

    def __str__(self):
        return f'{self.food_name} ({self.restaurant.name})'

# =========================================================================


class Badge(models.Model):
    
   # A donor achievement badge, e.g. 'Bronze Donor', 'Verified Partner'.
    #Awarded automatically based on a restaurant's total_donated_kg,
    #or manually via admin for special recognition badges (threshold_kg=None).
    
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=300, blank=True)

    # kg of total donations needed to auto-earn this badge.
    # Leave blank/null for badges that are awarded manually (not by threshold).
    threshold_kg = models.FloatField(null=True, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['threshold_kg']

    def __str__(self):
        return self.name



# ---------------------------------------------------------------------------
# Point 6: audit trail for (re)assignments, since Donation only stores the
# *current* agent and overwrites history on reassignment/expiry.
# ---------------------------------------------------------------------------

class AssignmentLog(models.Model):
    ACTION_CHOICES = [
        ('assigned', 'Assigned'),
        ('reassigned', 'Reassigned'),
        ('expired', 'Expired'),
        ('picked_up', 'Picked up'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    donation = models.ForeignKey(Donation, on_delete=models.CASCADE, related_name='assignment_logs')
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    notes = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return f'{self.donation_id} - {self.action} - {self.created_at:%Y-%m-%d %H:%M}'


# ---------------------------------------------------------------------------
# Point 7: feedback / rating for quality control on both sides
# ---------------------------------------------------------------------------

class Rating(models.Model):
    """A recipient (or admin, depending on your workflow) rates a completed
    donation's restaurant and/or the delivering agent."""

    donation = models.OneToOneField(Donation, on_delete=models.CASCADE, related_name='rating')

    restaurant_rating = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text='1-5 stars for the restaurant.'
    )
    agent_rating = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text='1-5 stars for the delivery agent.'
    )
    comments = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(restaurant_rating__isnull=True) | models.Q(restaurant_rating__gte=1, restaurant_rating__lte=5),
                name='rating_restaurant_1_to_5',
            ),
            models.CheckConstraint(
                condition=models.Q(agent_rating__isnull=True) | models.Q(agent_rating__gte=1, agent_rating__lte=5),
                name='rating_agent_1_to_5',
            ),
        ]

    def clean(self):
        for field_name in ('restaurant_rating', 'agent_rating'):
            value = getattr(self, field_name)
            if value is not None and not (1 <= value <= 5):
                raise ValidationError(f'{field_name} must be between 1 and 5.')

    def __str__(self):
        return f'Rating for donation {self.donation_id}'