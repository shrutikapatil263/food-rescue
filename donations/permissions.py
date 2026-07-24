"""
Place at: donations/permissions.py
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Used on Restaurant / Recipient / Agent viewsets.
    Anyone can read (list/retrieve); only the owning user can
    update/delete their own profile object.
    Assumes each model has a `user` FK to the auth user.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'user_id', None) == request.user.id


class IsDonationRestaurantOwnerOrReadOnly(permissions.BasePermission):
    """
    Used on Donation-related views.
    Anyone can read; only the restaurant that posted the donation
    can modify/delete it.
    Assumes Donation has a `restaurant` FK, and Restaurant has `user`.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        restaurant = getattr(obj, 'restaurant', None)
        return restaurant is not None and restaurant.user_id == request.user.id


class IsAssignedAgentOrRestaurantOwner(permissions.BasePermission):
    """
    Used for actions like update-status on a Donation.
    Allows either the agent currently assigned to the donation,
    or the restaurant that posted it, to act on it.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        assigned_agent = getattr(obj, 'assigned_agent', None)
        if assigned_agent is not None and getattr(assigned_agent, 'user_id', None) == user.id:
            return True

        restaurant = getattr(obj, 'restaurant', None)
        if restaurant is not None and getattr(restaurant, 'user_id', None) == user.id:
            return True

        return False