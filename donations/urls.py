"""
Place at: donations/urls.py (new file)
"""

from rest_framework.routers import DefaultRouter

from .views import (
    AgentViewSet,
    AssignmentLogViewSet,
    DonationViewSet,
    RatingViewSet,
    RecipientViewSet,
    RestaurantViewSet,
)

router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet)
router.register(r'recipients', RecipientViewSet)
router.register(r'agents', AgentViewSet)
router.register(r'donations', DonationViewSet)
router.register(r'assignment-logs', AssignmentLogViewSet)
router.register(r'ratings', RatingViewSet)

urlpatterns = router.urls
