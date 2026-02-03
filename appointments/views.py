from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta

from accounts.permissions import IsDonor
from .models import AppointmentSlot, Appointment, HealthQuestionnaire
from .serializers import AppointmentSlotSerializer, AppointmentSerializer, HealthQuestionnaireSerializer


class AppointmentSlotViewSet(viewsets.ViewSet):
    """
    API endpoints for appointment slot management and availability
    """
    # Allow public read access to view available slots (anonymous users should be able to browse)
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        """List available appointment slots with filters"""
        city = request.query_params.get('city')
        date_from = request.query_params.get('date_from')
        blood_bank = request.query_params.get('blood_bank')
        
        queryset = AppointmentSlot.objects.filter(status='available').order_by('date', 'start_time')
        
        if city:
            queryset = queryset.filter(city__iexact=city)
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if blood_bank:
            queryset = queryset.filter(blood_bank=blood_bank)
        
        serializer = AppointmentSlotSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get details of a specific appointment slot"""
        try:
            slot = AppointmentSlot.objects.get(pk=pk)
            serializer = AppointmentSlotSerializer(slot)
            return Response(serializer.data)
        except AppointmentSlot.DoesNotExist:
            return Response({'error': 'Slot not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_city(self, request):
        """Get slots available in a specific city"""
        city = request.query_params.get('city')
        if not city:
            return Response({'error': 'city parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        slots = AppointmentSlot.objects.filter(
            city__iexact=city,
            status='available'
        ).order_by('date', 'start_time')
        
        serializer = AppointmentSlotSerializer(slots, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get slots available in next 30 days"""
        today = timezone.now().date()
        thirty_days = today + timedelta(days=30)
        
        slots = AppointmentSlot.objects.filter(
            status='available',
            date__range=[today, thirty_days]
        ).order_by('date', 'start_time')
        
        serializer = AppointmentSlotSerializer(slots, many=True)
        return Response(serializer.data)


class AppointmentViewSet(viewsets.ViewSet):
    """
    API endpoints for appointment booking and management
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get donor's own appointments"""
        appointments = Appointment.objects.filter(donor=request.user).order_by('-booked_at')
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Book a new appointment"""
        serializer = AppointmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            try:
                appointment = serializer.save()
                # Increment booked donors count
                appointment.slot.booked_donors += 1
                if appointment.slot.booked_donors >= appointment.slot.max_donors:
                    appointment.slot.status = 'booked'
                appointment.slot.save()
                
                return Response(AppointmentSerializer(appointment).data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        """Get specific appointment details"""
        try:
            appointment = Appointment.objects.get(pk=pk, donor=request.user)
            serializer = AppointmentSerializer(appointment)
            return Response(serializer.data)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm appointment"""
        try:
            appointment = Appointment.objects.get(pk=pk, donor=request.user)
            appointment.is_confirmed_by_donor = True
            appointment.confirmed_at = timezone.now()
            appointment.status = 'confirmed'
            appointment.save()
            return Response(AppointmentSerializer(appointment).data)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel appointment"""
        try:
            appointment = Appointment.objects.get(pk=pk, donor=request.user)
            if appointment.status in ['completed', 'cancelled']:
                return Response(
                    {'error': f'Cannot cancel a {appointment.status} appointment'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            appointment.status = 'cancelled'
            appointment.slot.booked_donors -= 1
            appointment.slot.status = 'available'
            appointment.slot.save()
            appointment.save()
            return Response(AppointmentSerializer(appointment).data)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Mark appointment as completed (admin only)"""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            appointment = Appointment.objects.get(pk=pk)
            appointment.status = 'completed'
            appointment.donation_completed = True
            appointment.completed_at = timezone.now()
            appointment.units_donated = request.data.get('units_donated', 1)
            appointment.save()
            return Response(AppointmentSerializer(appointment).data)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)


class HealthQuestionnaireView(APIView):
    """
    Submit and manage health questionnaire for appointment
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, appointment_id):
        """Submit health questionnaire"""
        try:
            appointment = Appointment.objects.get(pk=appointment_id, donor=request.user)
        except Appointment.DoesNotExist:
            return Response({'error': 'Appointment not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if questionnaire already exists
        questionnaire, created = HealthQuestionnaire.objects.get_or_create(appointment=appointment)
        
        serializer = HealthQuestionnaireSerializer(questionnaire, data=request.data, partial=True)
        if serializer.is_valid():
            questionnaire = serializer.save()
            appointment.has_answered_health_questions = True
            appointment.health_check_passed = questionnaire.is_eligible
            appointment.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, appointment_id):
        """Get health questionnaire"""
        try:
            appointment = Appointment.objects.get(pk=appointment_id, donor=request.user)
            questionnaire = HealthQuestionnaire.objects.get(appointment=appointment)
            serializer = HealthQuestionnaireSerializer(questionnaire)
            return Response(serializer.data)
        except (Appointment.DoesNotExist, HealthQuestionnaire.DoesNotExist):
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

