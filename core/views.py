from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import BloodGroupCompatibility, BloodBank
from .serializers import BloodGroupCompatibilitySerializer, BloodBankSerializer


class BloodGroupCompatibilityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read endpoint so clients can understand compatibility rules.
    Admins can manage full table in Django admin.
    """

    queryset = BloodGroupCompatibility.objects.all().order_by("donor_group", "recipient_group")
    serializer_class = BloodGroupCompatibilitySerializer
    permission_classes = [permissions.AllowAny]


class BloodBankViewSet(viewsets.ViewSet):
    """
    API endpoints for finding blood banks and donation centers
    """
    permission_classes = [permissions.AllowAny]
    
    def list(self, request):
        """Get all active blood banks"""
        banks = BloodBank.objects.filter(is_active=True).order_by('city', 'name')
        serializer = BloodBankSerializer(banks, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, pk=None):
        """Get specific blood bank details"""
        try:
            bank = BloodBank.objects.get(pk=pk, is_active=True)
            serializer = BloodBankSerializer(bank)
            return Response(serializer.data)
        except BloodBank.DoesNotExist:
            return Response({'error': 'Blood bank not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['get'])
    def by_city(self, request):
        """Get blood banks in a specific city"""
        city = request.query_params.get('city')
        if not city:
            return Response({'error': 'city parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        banks = BloodBank.objects.filter(city__iexact=city, is_active=True)
        serializer = BloodBankSerializer(banks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Find nearby blood banks using coordinates"""
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius_km = float(request.query_params.get('radius', 50))
        
        if not lat or not lon:
            return Response(
                {'error': 'lat and lon parameters required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from django.db.models import F
            from math import asin, cos, radians, sin, sqrt
            
            lat, lon = float(lat), float(lon)
            
            # Haversine formula to calculate distance
            banks = BloodBank.objects.filter(is_active=True)
            results = []
            
            for bank in banks:
                # Simple distance calculation
                distance = calculate_distance(lat, lon, float(bank.latitude), float(bank.longitude))
                if distance <= radius_km:
                    results.append((distance, bank))
            
            # Sort by distance
            results.sort(key=lambda x: x[0])
            banks_sorted = [bank for _, bank in results]
            
            serializer = BloodBankSerializer(banks_sorted, many=True)
            return Response(serializer.data)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid coordinates'}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def open_now(self, request):
        """Get blood banks currently open"""
        from django.utils import timezone
        
        now = timezone.now().time()
        banks = BloodBank.objects.filter(
            is_active=True,
            opening_time__lte=now,
            closing_time__gte=now
        )
        
        serializer = BloodBankSerializer(banks, many=True)
        return Response(serializer.data)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in km (Haversine formula)"""
    from math import asin, cos, radians, sin, sqrt
    
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6371 * c
    return km

