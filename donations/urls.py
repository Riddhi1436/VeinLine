from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import BloodBankInventoryViewSet, DonorMeView, DonorStatisticsView, LeaderboardViewSet, DonorFeedbackViewSet

router = DefaultRouter()
router.register(r"inventory", BloodBankInventoryViewSet, basename="inventory")
router.register(r"leaderboard", LeaderboardViewSet, basename="leaderboard")
router.register(r"feedback", DonorFeedbackViewSet, basename="feedback")

urlpatterns = [
    path("donor/me/", DonorMeView.as_view(), name="donor-me"),
    path("donor/stats/", DonorStatisticsView.as_view(), name="donor-stats"),
]

urlpatterns += router.urls


