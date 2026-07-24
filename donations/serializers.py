from rest_framework import serializers

from .models import Agent, AssignmentLog, Donation, Rating, Recipient, Restaurant


class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = '__all__'
        read_only_fields = ('date_joined', 'updated_at', 'total_donated_kg', 'verification_status')


class RecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipient
        fields = '__all__'
        read_only_fields = ('date_joined', 'updated_at', 'verification_status')


class AgentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agent
        fields = '__all__'
        read_only_fields = (
            'date_joined', 'updated_at', 'completed_deliveries', 'verification_status',
        )


class AssignmentLogSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source='agent.name', read_only=True, default=None)

    class Meta:
        model = AssignmentLog
        fields = '__all__'
        read_only_fields = ('created_at',)


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ('created_at',)


class DonationSerializer(serializers.ModelSerializer):
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    assigned_agent_name = serializers.CharField(source='assigned_agent.name', read_only=True, default=None)
    assignment_logs = AssignmentLogSerializer(many=True, read_only=True)
    rating = RatingSerializer(read_only=True)

    class Meta:
        model = Donation
        fields = '__all__'
        read_only_fields = (
            'posted_at', 'updated_at', 'status', 'assigned_agent', 'assigned_at',
            'verification_status',
        )


class NearbyAgentSerializer(serializers.Serializer):
    """Used only for the 'nearby agents' read-only response, not tied to a model save."""
    id = serializers.IntegerField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    distance_km = serializers.FloatField()
    service_radius_km = serializers.FloatField()
    availability_status = serializers.CharField()