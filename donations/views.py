from rest_framework import permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from django.db.models import Q, Avg
from django.db import models

from accounts.permissions import IsDonor
from .models import BloodBankInventory, DonorDetails, DonorStatistics, DonorFeedback
from .serializers import BloodBankInventorySerializer, DonorDetailsSerializer, DonorStatisticsSerializer, LeaderboardSerializer, DonorFeedbackSerializer


class DonorMeView(APIView):
    """
    Donor can view/update their own donor details.
    """

    permission_classes = [permissions.IsAuthenticated, IsDonor]

    def get(self, request):
        details = DonorDetails.objects.get(user=request.user)
        return Response(DonorDetailsSerializer(details).data)

    def patch(self, request):
        details = DonorDetails.objects.get(user=request.user)
        ser = DonorDetailsSerializer(details, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(ser.data, status=status.HTTP_200_OK)


class BloodBankInventoryViewSet(viewsets.ModelViewSet):
    """
    Admin-managed inventory; readable by authenticated users.
    """

    queryset = BloodBankInventory.objects.all().order_by("city", "blood_group")
    serializer_class = BloodBankInventorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [permissions.IsAdminUser()]
        return super().get_permissions()


class DonorStatisticsView(APIView):
    """
    Get donor's own statistics and badges.
    """
    permission_classes = [permissions.IsAuthenticated, IsDonor]

    def get(self, request):
        stats, created = DonorStatistics.objects.get_or_create(donor=request.user)
        return Response(DonorStatisticsSerializer(stats).data)


class LeaderboardViewSet(viewsets.ViewSet):
    """
    Public leaderboard of top donors
    """
    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=['get'])
    def top_donors(self, request):
        """Get top 100 donors by points"""
        limit = int(request.query_params.get('limit', 100))
        stats = DonorStatistics.objects.filter(points__gt=0).order_by('-points')[:limit]
        
        # Update ranks
        for idx, stat in enumerate(stats, 1):
            stat.rank = idx
            stat.save()
        
        serializer = LeaderboardSerializer(stats, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_city(self, request):
        """Get top donors by city"""
        city = request.query_params.get('city')
        if not city:
            return Response({"error": "city parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        
        stats = DonorStatistics.objects.filter(
            points__gt=0,
            donor__donor_details__city__iexact=city
        ).order_by('-points')[:50]
        
        serializer = LeaderboardSerializer(stats, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_blood_group(self, request):
        """Get top donors by blood group"""
        blood_group = request.query_params.get('blood_group')
        if not blood_group:
            return Response({"error": "blood_group parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        
        stats = DonorStatistics.objects.filter(
            points__gt=0,
            donor__donor_details__blood_group=blood_group
        ).order_by('-points')[:50]
        
        serializer = LeaderboardSerializer(stats, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def badges(self, request):
        """Get all available badges with descriptions"""
        from .models import Badge
        badges = [
            {'key': key, 'label': value} for key, value in Badge.choices
        ]
        return Response(badges)

class DonorFeedbackViewSet(viewsets.ViewSet):
    """
    API endpoints for donor feedback and testimonials
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get feedback for a specific donor"""
        donor_id = request.query_params.get('donor_id')
        if not donor_id:
            return Response({'error': 'donor_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        feedback = DonorFeedback.objects.filter(donor_id=donor_id, is_public=True).order_by('-created_at')
        serializer = DonorFeedbackSerializer(feedback, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Leave feedback for a donor"""
        serializer = DonorFeedbackSerializer(data=request.data)
        if serializer.is_valid():
            # Patient is the current user
            serializer.validated_data['patient'] = request.user
            feedback = serializer.save()
            return Response(DonorFeedbackSerializer(feedback).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_feedback(self, request):
        """Get feedback about current user (for donors to see)"""
        feedback = DonorFeedback.objects.filter(donor=request.user, is_public=True).order_by('-created_at')
        serializer = DonorFeedbackSerializer(feedback, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get feedback statistics for a donor"""
        donor_id = request.query_params.get('donor_id')
        if not donor_id:
            return Response({'error': 'donor_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        feedback = DonorFeedback.objects.filter(donor_id=donor_id, is_public=True)
        
        if not feedback.exists():
            return Response({
                'total_feedback': 0,
                'average_rating': 0,
                'distribution': {}
            })
        
        total = feedback.count()
        avg_rating = feedback.aggregate(avg=models.Avg('rating'))['avg'] or 0
        
        distribution = {}
        for rating_value, _ in DonorFeedback.RATING_CHOICES:
            distribution[rating_value] = feedback.filter(rating=rating_value).count()
        
        return Response({
            'total_feedback': total,
            'average_rating': round(avg_rating, 1),
            'distribution': distribution,
        })