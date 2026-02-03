from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


class NotificationViewSet(viewsets.ViewSet):
    """
    API endpoints for managing notifications
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get user's notifications"""
        notifications = Notification.objects.filter(recipient=request.user)
        
        # Filter by read status if requested
        is_read = request.query_params.get('is_read')
        if is_read is not None:
            is_read = is_read.lower() == 'true'
            notifications = notifications.filter(is_read=is_read)
        
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get all unread notifications"""
        notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark a notification as read"""
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.mark_as_read()
            return Response(NotificationSerializer(notification).data)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        """Mark all notifications as read for the user"""
        notifications = Notification.objects.filter(recipient=request.user, is_read=False)
        count = notifications.count()
        
        from django.utils import timezone
        notifications.update(is_read=True, read_at=timezone.now())
        
        return Response({'marked_as_read': count})
    
    @action(detail=True, methods=['delete'])
    def delete_notification(self, request, pk=None):
        """Delete a notification"""
        try:
            notification = Notification.objects.get(pk=pk, recipient=request.user)
            notification.delete()
            return Response({'status': 'deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def delete_all(self, request):
        """Delete all notifications for the user"""
        notifications = Notification.objects.filter(recipient=request.user)
        count = notifications.count()
        notifications.delete()
        return Response({'deleted': count})
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get notifications filtered by type"""
        notification_type = request.query_params.get('type')
        if not notification_type:
            return Response({'error': 'type parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        notifications = Notification.objects.filter(
            recipient=request.user,
            notification_type=notification_type
        )
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class NotificationPreferenceView(APIView):
    """
    Manage user notification preferences
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user's notification preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs)
        return Response(serializer.data)
    
    def patch(self, request):
        """Update user's notification preferences"""
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

