from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DonationDriveViewSet,
    DriveRegistrationViewSet,
    DonationCertificateViewSet,
    DonorAvailabilitySlotViewSet,
)

router = DefaultRouter()
router.register('drives', DonationDriveViewSet, basename='donation-drive')
router.register('drive-registrations', DriveRegistrationViewSet, basename='drive-registration')
router.register('certificates', DonationCertificateViewSet, basename='certificate')
router.register('availability', DonorAvailabilitySlotViewSet, basename='availability')

urlpatterns = [
    path('', include(router.urls)),
]
