from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, NotificationPreferenceView

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notifications')

urlpatterns = [
    path('notifications/preferences/', NotificationPreferenceView.as_view(), name='notification-preferences'),
]

urlpatterns += router.urls
