from rest_framework.routers import DefaultRouter

from .views import (
    InboundSMSViewSet,
    SOSRequestViewSet,
    SOSResponseViewSet,
    DonationTrackerViewSet,
    MessageViewSet,
    EmergencyContactViewSet,
)

router = DefaultRouter()
router.register(r"sos/requests", SOSRequestViewSet, basename="sos-requests")
router.register(r"sos/responses", SOSResponseViewSet, basename="sos-responses")
router.register(r"sos/tracker", DonationTrackerViewSet, basename="donation-tracker")
router.register(r"messages", MessageViewSet, basename="messages")
router.register(r"emergency-contacts", EmergencyContactViewSet, basename="emergency-contacts")
router.register(r"sms", InboundSMSViewSet, basename="sms")

urlpatterns = router.urls


