from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import AppointmentSlotViewSet, AppointmentViewSet, HealthQuestionnaireView

router = DefaultRouter()
router.register(r'slots', AppointmentSlotViewSet, basename='appointment-slots')
router.register(r'my-appointments', AppointmentViewSet, basename='my-appointments')

urlpatterns = [
    path('appointments/<int:appointment_id>/health-questionnaire/', HealthQuestionnaireView.as_view(), name='health-questionnaire'),
]

urlpatterns += router.urls
