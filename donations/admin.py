from django.contrib import admin
from .models import Restaurant, Recipient, Agent, Donation, AssignmentLog, Rating


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'owner_name', 'cuisine_type', 'verification_status',
        'is_active', 'total_donated_kg', 'date_joined',
    )
    list_filter = ('verification_status', 'cuisine_type', 'is_active')
    search_fields = ('name', 'owner_name', 'email', 'phone_number', 'address')
    readonly_fields = ('date_joined', 'updated_at', 'total_donated_kg')
    autocomplete_fields = ('user',)


@admin.register(Recipient)
class RecipientAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'recipient_type', 'contact_person', 'capacity_people',
        'verification_status', 'is_active', 'date_joined',
    )
    list_filter = ('verification_status', 'recipient_type', 'is_active')
    search_fields = ('name', 'contact_person', 'email', 'phone_number', 'address')
    readonly_fields = ('date_joined', 'updated_at')
    autocomplete_fields = ('user',)


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'availability_status', 'verification_status',
        'completed_deliveries', 'service_radius_km', 'is_active', 'last_location_update',
    )
    list_filter = ('availability_status', 'verification_status', 'is_active')
    search_fields = ('name', 'email', 'phone_number')
    readonly_fields = ('date_joined', 'updated_at', 'completed_deliveries')
    autocomplete_fields = ('user',)


class AssignmentLogInline(admin.TabularInline):
    model = AssignmentLog
    extra = 0
    readonly_fields = ('action', 'agent', 'notes', 'created_at')
    can_delete = False


class RatingInline(admin.StackedInline):
    model = Rating
    extra = 0
    can_delete = False


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = (
        'food_name', 'restaurant', 'status', 'assigned_agent',
        'quantity_kg', 'verification_status', 'pickup_deadline',
    )
    list_filter = (
        'status', 'verification_status', 'food_category',
        'storage_condition', 'pickup_deadline',
    )
    search_fields = (
        'food_name', 'restaurant__name', 'assigned_agent__name',
        'pickup_address', 'delivery_address',
    )
    autocomplete_fields = ('restaurant', 'recipient', 'assigned_agent')
    readonly_fields = ('posted_at', 'updated_at')
    date_hierarchy = 'pickup_deadline'
    inlines = [AssignmentLogInline, RatingInline]


@admin.register(AssignmentLog)
class AssignmentLogAdmin(admin.ModelAdmin):
    list_display = ('donation', 'action', 'agent', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('donation__food_name', 'agent__name', 'notes')
    autocomplete_fields = ('donation', 'agent')
    readonly_fields = ('created_at',)


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('donation', 'restaurant_rating', 'agent_rating', 'created_at')
    search_fields = ('donation__food_name',)
    autocomplete_fields = ('donation',)
    readonly_fields = ('created_at',)