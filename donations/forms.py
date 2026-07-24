"""
Place at: donations/forms.py
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Agent, Donation, Recipient, Restaurant


class RestaurantSignUpForm(UserCreationForm):
    """
    Creates a User + linked Restaurant profile in one step.
    Collects every Restaurant field that is required and has no default.
    """
    restaurant_name = forms.CharField(max_length=150, label="Restaurant name")
    owner_name = forms.CharField(max_length=150, label="Owner's name")
    restaurant_email = forms.EmailField(label="Restaurant contact email")
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(max_length=255)
    latitude = forms.FloatField(help_text="e.g. 16.6900")
    longitude = forms.FloatField(help_text="e.g. 74.4700")
    opening_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))
    closing_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}))

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Restaurant.objects.create(
                user=user,
                name=self.cleaned_data['restaurant_name'],
                owner_name=self.cleaned_data['owner_name'],
                email=self.cleaned_data['restaurant_email'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address'],
                latitude=self.cleaned_data['latitude'],
                longitude=self.cleaned_data['longitude'],
                opening_time=self.cleaned_data['opening_time'],
                closing_time=self.cleaned_data['closing_time'],
            )
        return user


class AgentSignUpForm(UserCreationForm):
    """
    Creates a User + linked Agent profile in one step.
    Agent model only requires name, phone_number, email beyond the user link
    — everything else (availability_status, service_radius_km, etc.) has a default.
    """
    agent_name = forms.CharField(max_length=150, label="Full name")
    agent_email = forms.EmailField(label="Contact email")
    phone_number = forms.CharField(max_length=20)
    service_radius_km = forms.FloatField(
        required=False,
        initial=5.0,
        help_text="How far you're willing to travel (km). Defaults to 5.",
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            kwargs = dict(
                user=user,
                name=self.cleaned_data['agent_name'],
                email=self.cleaned_data['agent_email'],
                phone_number=self.cleaned_data['phone_number'],
            )
            if self.cleaned_data.get('service_radius_km'):
                kwargs['service_radius_km'] = self.cleaned_data['service_radius_km']
            Agent.objects.create(**kwargs)
        return user


class RecipientSignUpForm(UserCreationForm):
    """
    Creates a User + linked Recipient (NGO/orphanage/shelter) profile.
    Collects every Recipient field that is required and has no default.
    """
    recipient_name = forms.CharField(max_length=150, label="Organization name")
    contact_person = forms.CharField(max_length=150)
    recipient_email = forms.EmailField(label="Contact email")
    phone_number = forms.CharField(max_length=20)
    address = forms.CharField(max_length=255)
    latitude = forms.FloatField(help_text="e.g. 16.6900")
    longitude = forms.FloatField(help_text="e.g. 74.4700")
    capacity_people = forms.IntegerField(label="People you can typically feed/serve", min_value=1)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            Recipient.objects.create(
                user=user,
                name=self.cleaned_data['recipient_name'],
                contact_person=self.cleaned_data['contact_person'],
                email=self.cleaned_data['recipient_email'],
                phone_number=self.cleaned_data['phone_number'],
                address=self.cleaned_data['address'],
                latitude=self.cleaned_data['latitude'],
                longitude=self.cleaned_data['longitude'],
                capacity_people=self.cleaned_data['capacity_people'],
            )
        return user


class DonationForm(forms.ModelForm):
    """
    Used by a logged-in restaurant to post a new donation.
    `restaurant` is set server-side from request.user, not exposed here.
    """
    class Meta:
        model = Donation
        fields = [
            'food_name',
            'quantity_kg',
            'estimated_servings',
            'prepared_at',
            'pickup_deadline',
            'food_category',
            'storage_condition',
            'food_image',
            'pickup_address',
            'delivery_address',
        ]
        widgets = {
            'food_name': forms.TextInput(attrs={
                'placeholder': 'e.g. Vegetable biryani, 20 servings',
                'autofocus': True,
            }),
            'quantity_kg': forms.NumberInput(attrs={
                'min': '0.1', 'step': '0.1', 'placeholder': 'e.g. 5.5',
            }),
            'estimated_servings': forms.NumberInput(attrs={
                'min': '1', 'placeholder': 'e.g. 20',
            }),
            'prepared_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'pickup_deadline': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'food_category': forms.Select(),
            'storage_condition': forms.Select(),
            'pickup_address': forms.TextInput(attrs={
                'placeholder': 'Where should the agent pick this up?',
            }),
            'delivery_address': forms.TextInput(attrs={
                'placeholder': 'Optional — leave blank if not yet decided',
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        prepared_at = cleaned_data.get('prepared_at')
        pickup_deadline = cleaned_data.get('pickup_deadline')
        quantity_kg = cleaned_data.get('quantity_kg')

        if prepared_at and pickup_deadline and pickup_deadline <= prepared_at:
            self.add_error(
                'pickup_deadline',
                'Pickup deadline must be after the prepared time.'
            )

        if quantity_kg is not None and quantity_kg <= 0:
            self.add_error(
                'quantity_kg',
                'Quantity must be greater than 0 kg.'
            )

        return cleaned_data