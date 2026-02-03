from rest_framework.routers import DefaultRouter

from .views import BloodGroupCompatibilityViewSet, BloodBankViewSet

router = DefaultRouter()
router.register(r"compatibility", BloodGroupCompatibilityViewSet, basename="compatibility")
router.register(r"blood-banks", BloodBankViewSet, basename="blood-banks")

urlpatterns = router.urls

