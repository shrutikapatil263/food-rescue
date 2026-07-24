"""
Place at: donations/views.py
(replaces/extends the default views.py Django created)
"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .assignment import assign_nearest_agent, release_agent
from .matching import get_available_agents_for_donation
from .models import Agent, AssignmentLog, Donation, Rating, Recipient, Restaurant
from .notifications import notify_status_change
from .permissions import (
    IsAssignedAgentOrRestaurantOwner,
    IsDonationRestaurantOwnerOrReadOnly,
    IsOwnerOrReadOnly,
)
from .serializers import (
    AgentSerializer,
    AssignmentLogSerializer,
    DonationSerializer,
    NearbyAgentSerializer,
    RatingSerializer,
    RecipientSerializer,
    RestaurantSerializer,
)

# Which current statuses are allowed to move to which next status.
# Mirrors the rules in the update_donation_status management command.
VALID_TRANSITIONS = {
    'picked_up': {'assigned'},
    'delivered': {'picked_up'},
    'cancelled': {'pending', 'assigned', 'picked_up'},
    'expired': {'assigned'},
}


class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all().order_by('-date_joined')
    serializer_class = RestaurantSerializer
    permission_classes = [IsOwnerOrReadOnly]


class RecipientViewSet(viewsets.ModelViewSet):
    queryset = Recipient.objects.all().order_by('-date_joined')
    serializer_class = RecipientSerializer
    permission_classes = [IsOwnerOrReadOnly]


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all().order_by('-date_joined')
    serializer_class = AgentSerializer
    permission_classes = [IsOwnerOrReadOnly]


class AssignmentLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AssignmentLog.objects.all().order_by('-created_at')
    serializer_class = AssignmentLogSerializer


class RatingViewSet(viewsets.ModelViewSet):
    queryset = Rating.objects.all().order_by('-created_at')
    serializer_class = RatingSerializer


class DonationViewSet(viewsets.ModelViewSet):
    queryset = Donation.objects.all().order_by('-posted_at')
    serializer_class = DonationSerializer

    @action(detail=True, methods=['get'], url_path='nearby-agents')
    def nearby_agents(self, request, pk=None):
        """GET /api/donations/{id}/nearby-agents/ — preview candidates without assigning."""
        donation = self.get_object()
        matches = get_available_agents_for_donation(donation)
        data = [
            {
                'id': agent.id,
                'name': agent.name,
                'phone_number': agent.phone_number,
                'distance_km': distance_km,
                'service_radius_km': agent.service_radius_km,
                'availability_status': agent.availability_status,
            }
            for agent, distance_km in matches
        ]
        return Response(NearbyAgentSerializer(data, many=True).data)

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        """POST /api/donations/{id}/assign/ — auto-assign nearest available agent."""
        donation = self.get_object()
        result = assign_nearest_agent(donation)

        if not result.success:
            return Response({'detail': result.reason}, status=status.HTTP_409_CONFLICT)

        donation.refresh_from_db()
        return Response(DonationSerializer(donation).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """
        POST /api/donations/{id}/update-status/
        Body: {"new_status": "picked_up" | "delivered" | "cancelled" | "expired"}
        """
        donation = self.get_object()
        new_status = request.data.get('new_status')

        if new_status not in VALID_TRANSITIONS:
            return Response(
                {'detail': f"new_status must be one of {list(VALID_TRANSITIONS.keys())}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed_from = VALID_TRANSITIONS[new_status]
        if donation.status not in allowed_from:
            return Response(
                {'detail': f"Cannot move from '{donation.status}' to '{new_status}'. "
                            f"Allowed only from: {sorted(allowed_from)}"},
                status=status.HTTP_409_CONFLICT,
            )

        donation.status = new_status
        donation.save(update_fields=['status', 'updated_at'])

        if new_status in ('delivered', 'cancelled', 'expired'):
            release_agent(donation, action=new_status)
        else:
            AssignmentLog.objects.create(
                donation=donation,
                agent=donation.assigned_agent,
                action=new_status,
            )
            notify_status_change(donation, new_status)

        donation.refresh_from_db()
        return Response(DonationSerializer(donation).data, status=status.HTTP_200_OK)