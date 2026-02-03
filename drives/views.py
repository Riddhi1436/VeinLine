from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DonationDrive, DriveRegistration, DonationCertificate, DonorAvailabilitySlot
from .serializers import (
    DonationDriveSerializer,
    DriveRegistrationSerializer,
    DonationCertificateSerializer,
    DonorAvailabilitySlotSerializer,
)
from notifications.services import NotificationService


class DonationDriveViewSet(viewsets.ModelViewSet):
    """Blood donation drives/events"""
    serializer_class = DonationDriveSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = DonationDrive.objects.all().order_by('-start_date')
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(city__iexact=city)
        
        # Only show published drives to non-staff users
        if not self.request.user.is_staff:
            queryset = queryset.filter(status__in=['published', 'ongoing', 'completed'])
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(organizer=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def register(self, request, pk=None):
        """Register for a donation drive"""
        drive = self.get_object()
        
        # Check if drive is full
        if drive.is_full():
            return Response({'detail': 'Drive is full'}, status=400)
        
        # Check if already registered
        if DriveRegistration.objects.filter(drive=drive, donor=request.user).exists():
            return Response({'detail': 'Already registered'}, status=400)
        
        # Create registration
        registration = DriveRegistration.objects.create(
            drive=drive,
            donor=request.user,
            status='registered'
        )
        
        # Update drive registration count
        drive.current_registrations += 1
        drive.save(update_fields=['current_registrations'])
        
        # Send confirmation notification
        NotificationService.notify_custom(
            request.user,
            f"Registration Confirmed: {drive.title}",
            f"You have successfully registered for {drive.title} on {drive.start_date}",
            notification_type='appointment_reminder'
        )
        
        return Response(DriveRegistrationSerializer(registration).data, status=201)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming drives"""
        today = timezone.now().date()
        queryset = DonationDrive.objects.filter(
            start_date__gte=today,
            status='published'
        ).order_by('start_date')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DriveRegistrationViewSet(viewsets.ModelViewSet):
    """Drive registration management"""
    serializer_class = DriveRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return DriveRegistration.objects.all().select_related('drive', 'donor')
        
        # Donors see their own registrations
        return DriveRegistration.objects.filter(donor=user).select_related('drive')
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel registration"""
        registration = self.get_object()
        
        # Ensure user owns this registration
        if registration.donor_id != request.user.id and not request.user.is_staff:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        
        if registration.status == 'cancelled':
            return Response({'detail': 'Already cancelled'}, status=400)
        
        registration.status = 'cancelled'
        registration.save(update_fields=['status'])
        
        # Update drive registration count
        drive = registration.drive
        drive.current_registrations = max(0, drive.current_registrations - 1)
        drive.save(update_fields=['current_registrations'])
        
        return Response(self.get_serializer(registration).data)


class DonationCertificateViewSet(viewsets.ModelViewSet):
    """Donation certificates"""
    serializer_class = DonationCertificateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_staff:
            return DonationCertificate.objects.all()
        
        # Donors see their own certificates
        return DonationCertificate.objects.filter(donor=user).order_by('-issued_at')
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Download certificate PDF (placeholder - requires PDF generation library)"""
        certificate = self.get_object()
        
        if certificate.donor_id != request.user.id and not request.user.is_staff:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        
        # TODO: Implement actual PDF generation using ReportLab or WeasyPrint
        # For now, return certificate data
        return Response({
            'certificate_number': certificate.certificate_number,
            'donor_name': certificate.donor.get_full_name() or certificate.donor.username,
            'blood_group': certificate.blood_group,
            'units_donated': certificate.units_donated,
            'donation_date': certificate.donation_date,
            'location': certificate.location,
            'qr_code_data': certificate.qr_code_data,
            'message': 'PDF generation not yet implemented. Use this data to generate certificate.'
        })
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """Increment share count"""
        certificate = self.get_object()
        
        if certificate.donor_id != request.user.id and not request.user.is_staff:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        
        certificate.share_count += 1
        certificate.save(update_fields=['share_count'])
        
        return Response({'share_count': certificate.share_count})


class DonorAvailabilitySlotViewSet(viewsets.ModelViewSet):
    """Donor availability calendar"""
    serializer_class = DonorAvailabilitySlotSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Only donors can manage availability
        return DonorAvailabilitySlot.objects.filter(donor=user)
    
    def perform_create(self, serializer):
        serializer.save(donor=self.request.user)
    
    @action(detail=False, methods=['get'])
    def check_availability(self, request):
        """Check if donor is available on a specific date"""
        date_str = request.query_params.get('date')
        
        if not date_str:
            return Response({'detail': 'date parameter required'}, status=400)
        
        from datetime import datetime
        try:
            check_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'detail': 'Invalid date format. Use YYYY-MM-DD'}, status=400)
        
        # Check specific date
        specific = DonorAvailabilitySlot.objects.filter(
            donor=request.user,
            date=check_date
        ).first()
        
        if specific:
            return Response({
                'is_available': specific.availability_type == 'available',
                'availability_type': specific.availability_type,
                'reason': specific.reason,
                'auto_response': specific.auto_response_message,
            })
        
        # Check recurring availability
        day_of_week = check_date.weekday()
        recurring = DonorAvailabilitySlot.objects.filter(
            donor=request.user,
            is_recurring=True,
            day_of_week=day_of_week
        ).first()
        
        if recurring:
            return Response({
                'is_available': recurring.availability_type == 'available',
                'availability_type': recurring.availability_type,
                'reason': recurring.reason,
                'auto_response': recurring.auto_response_message,
            })
        
        # Default: available
        return Response({'is_available': True, 'availability_type': 'available'})
