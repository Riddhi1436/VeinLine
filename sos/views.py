from __future__ import annotations

import logging
import re

from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsDonor, IsPatient
from core.services.emailing import send_fallback_email
from core.services.sms import send_sms
from donations.models import DonorDetails
from notifications.services import NotificationService
from .models import (
    DonationTracker,
    Message,
    EmergencyContact,
    ResponseChannel,
    ResponseChoice,
    SOSRequest,
    SOSResponse,
)
from .serializers import (
    DonationTrackerSerializer,
    EmergencyContactSerializer,
    InboundSMSSerializer,
    MessageSerializer,
    RespondSerializer,
    SOSRequestSerializer,
    SOSResponseSerializer,
)
from .services import match_donors_for_request

User = get_user_model()
logger = logging.getLogger(__name__)


def _normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone or "")
    return digits


def _find_user_by_phone(phone: str) -> User | None:
    """
    Best-effort matching by last 10 digits (works for many local formats).
    For production, enforce E.164 in registration and compare exact.
    """

    digits = _normalize_phone(phone)
    if not digits:
        return None
    last10 = digits[-10:]
    return User.objects.filter(profile__phone_e164__endswith=last10).first()


class SOSRequestViewSet(viewsets.ModelViewSet):
    serializer_class = SOSRequestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SOSRequest.objects.all().order_by("-created_at")
        # Patients see their own requests; donors can see open requests in their city for awareness.
        role = getattr(getattr(user, "profile", None), "role", "")
        if role == "patient":
            return SOSRequest.objects.filter(requester=user).order_by("-created_at")
        if role == "donor":
            city = getattr(getattr(user, "donor_details", None), "city", "")
            qs = SOSRequest.objects.filter(status="open").order_by("-created_at")
            if city:
                qs = qs.filter(city__iexact=city)
            return qs
        return SOSRequest.objects.none()

    def perform_create(self, serializer):
        serializer.save(requester=self.request.user)

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [permissions.IsAuthenticated(), IsPatient()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsPatient])
    def match(self, request, pk=None):
        """
        Rule-based matching + notifications:
        - Create pending SOSResponse rows for matched donors
        - Send SMS alerts (and email fallback if available)
        """

        sos_req: SOSRequest = self.get_object()
        donors = match_donors_for_request(sos_req, limit=50)

        notified = []
        sms_results = []
        
        with transaction.atomic():
            for d in donors:
                resp, created = SOSResponse.objects.get_or_create(
                    request=sos_req,
                    donor=d.user,
                    defaults={"response": ResponseChoice.PENDING, "channel": ResponseChannel.SMS},
                )
                notified.append({"donor_id": d.user_id, "created": created, "response_id": resp.id})

                # Notification message includes token for SMS reply.
                sms_message = (
                    f"VeinLine SOS: Need {sos_req.blood_group_needed} blood in {sos_req.city}. "
                    f"Reply: YES {sos_req.sms_reply_token} or NO {sos_req.sms_reply_token}."
                    f" (Optional consent: YES SHARE {sos_req.sms_reply_token})"
                )

                # Get donor phone number
                phone = getattr(getattr(d.user, "profile", None), "phone_e164", "")
                if phone:
                    try:
                        sms_result = send_sms(phone, sms_message)
                        sms_results.append({
                            "donor_id": d.user_id,
                            "donor_name": d.full_name,
                            "phone": phone,
                            "sms": sms_result
                        })
                        # Log SMS sending
                        logger.info(f"SMS sent to donor {d.user_id} ({phone}) for SOS request {sos_req.id}")
                    except Exception as e:
                        logger.error(f"Failed to send SMS to donor {d.user_id}: {str(e)}")
                        sms_results.append({
                            "donor_id": d.user_id,
                            "donor_name": d.full_name,
                            "phone": phone,
                            "error": str(e)
                        })
                else:
                    logger.warning(f"No phone number for donor {d.user_id} ({d.full_name})")
                    sms_results.append({
                        "donor_id": d.user_id,
                        "donor_name": d.full_name,
                        "phone": None,
                        "skipped": "No phone number"
                    })

                # Email fallback (if donor has email)
                try:
                    send_fallback_email(
                        to_email=getattr(d.user, "email", ""),
                        subject="VeinLine SOS Alert",
                        message=sms_message,
                    )
                except Exception as e:
                    logger.error(f"Failed to send email to donor {d.user_id}: {str(e)}")

        return Response(
            {
                "request_id": sos_req.id,
                "matched_donors": len(donors) if hasattr(donors, "__len__") else donors.count(),
                "responses_created_or_found": notified,
                "sms_results": sms_results,
                "message": f"SOS notification sent to {len(sms_results)} donors"
            },
            status=status.HTTP_200_OK
        )


class SOSResponseViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SOSResponseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return SOSResponse.objects.select_related("request", "donor").all().order_by("-created_at")
        role = getattr(getattr(user, "profile", None), "role", "")
        if role == "patient":
            return SOSResponse.objects.select_related("request", "donor").filter(request__requester=user).order_by(
                "-created_at"
            )
        if role == "donor":
            return SOSResponse.objects.select_related("request", "donor").filter(donor=user).order_by("-created_at")
        return SOSResponse.objects.none()

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsDonor])
    def respond(self, request, pk=None):
        """
        Donor responds (YES/NO) and may optionally consent to share contact for this request.
        """

        sos_resp: SOSResponse = self.get_object()
        if sos_resp.donor_id != request.user.id and not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        ser = RespondSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        ser.save(sos_response=sos_resp)
        
        # Notify patient of donor's response
        patient = sos_resp.request.requester
        donor_name = getattr(getattr(sos_resp.donor, 'donor_details', None), 'full_name', sos_resp.donor.username)
        response_text = "agreed to help" if sos_resp.response == 'yes' else "declined"
        NotificationService.notify_custom(
            patient,
            f"Donor Response: {donor_name}",
            f"{donor_name} has {response_text} for your SOS request.",
            notification_type='sos_alert'
        )
        
        # If donor agreed, create tracking
        if sos_resp.response == 'yes':
            DonationTracker.objects.get_or_create(
                sos_response=sos_resp,
                defaults={'current_status': 'agreed'}
            )
        
        return Response(SOSResponseSerializer(sos_resp, context={"request": request}).data)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsPatient])
    def reveal_contact(self, request, pk=None):
        """
        Patient "reveals" contact if donor consented; we track reveal timestamp.
        """

        sos_resp: SOSResponse = self.get_object()
        if sos_resp.request.requester_id != request.user.id and not request.user.is_staff:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        if not sos_resp.donor_consented_to_share_contact:
            return Response({"detail": "Donor has not consented to share contact yet."}, status=400)

        sos_resp.patient_contact_revealed_at = timezone.now()
        sos_resp.save(update_fields=["patient_contact_revealed_at"])
        return Response(SOSResponseSerializer(sos_resp, context={"request": request}).data)


class InboundSMSViewSet(viewsets.ViewSet):
    """
    Provider webhook for SMS replies. Keep it simple: accept normalized JSON.
    You can configure Fast2SMS/Textlocal to call this endpoint, or a small proxy.
    """

    permission_classes = [permissions.AllowAny]

    @action(detail=False, methods=["post"], url_path="inbound")
    def inbound(self, request):
        ser = InboundSMSSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        from_phone = ser.validated_data["from_phone"]
        message = ser.validated_data["message"].strip().upper()

        # Parse: YES <token> | NO <token> | YES SHARE <token>
        parts = re.split(r"\s+", message)
        if not parts:
            return Response({"ok": False, "error": "empty_message"}, status=400)

        decision = parts[0]
        wants_share = "SHARE" in parts[1:-1] if len(parts) >= 3 else False
        token = parts[-1] if len(parts) >= 2 else ""

        if decision not in {"YES", "NO"} or not token:
            return Response({"ok": False, "error": "invalid_format"}, status=400)

        sos_req = SOSRequest.objects.filter(sms_reply_token=token).first()
        if not sos_req:
            return Response({"ok": False, "error": "invalid_token"}, status=404)

        user = _find_user_by_phone(from_phone)
        if not user:
            return Response({"ok": False, "error": "unknown_phone"}, status=404)

        # Ensure donor has donor details (role safety)
        if not hasattr(user, "donor_details"):
            return Response({"ok": False, "error": "not_a_donor"}, status=400)

        sos_resp, _ = SOSResponse.objects.get_or_create(
            request=sos_req,
            donor=user,
            defaults={"response": ResponseChoice.PENDING, "channel": ResponseChannel.SMS},
        )

        sos_resp.response = ResponseChoice.YES if decision == "YES" else ResponseChoice.NO
        sos_resp.channel = ResponseChannel.SMS
        sos_resp.responded_at = timezone.now()
        if wants_share and decision == "YES":
            sos_resp.donor_consented_to_share_contact = True
        sos_resp.save(
            update_fields=["response", "channel", "responded_at", "donor_consented_to_share_contact"]
        )

        return Response({"ok": True, "request_id": sos_req.id, "response_id": sos_resp.id, "response": sos_resp.response})


class DonationTrackerViewSet(viewsets.ModelViewSet):
    """Live donation tracking"""
    serializer_class = DonationTrackerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return DonationTracker.objects.all()
        
        # Donors see their own trackers, patients see trackers for their SOS requests
        role = getattr(getattr(user, 'profile', None), 'role', '')
        if role == 'donor':
            return DonationTracker.objects.filter(sos_response__donor=user)
        elif role == 'patient':
            return DonationTracker.objects.filter(sos_response__request__requester=user)
        return DonationTracker.objects.none()
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsDonor])
    def update_status(self, request, pk=None):
        """Update donation status"""
        tracker = self.get_object()
        
        # Ensure donor owns this tracker
        if tracker.sos_response.donor_id != request.user.id and not request.user.is_staff:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        
        new_status = request.data.get('status')
        if new_status not in dict(DonationTracker._meta.get_field('current_status').choices):
            return Response({'detail': 'Invalid status.'}, status=400)
        
        tracker.update_status(new_status)
        
        # Update location if provided
        if 'latitude' in request.data and 'longitude' in request.data:
            tracker.current_latitude = request.data['latitude']
            tracker.current_longitude = request.data['longitude']
            tracker.save(update_fields=['current_latitude', 'current_longitude'])
        
        # Notify patient of status update
        patient = tracker.sos_response.request.requester
        NotificationService.notify_custom(
            patient,
            f"Donor Status Update: {tracker.get_current_status_display()}",
            f"Your donor has updated their status to {tracker.get_current_status_display()}",
            notification_type='sos_alert'
        )
        
        return Response(DonationTrackerSerializer(tracker, context={'request': request}).data)


class MessageViewSet(viewsets.ModelViewSet):
    """Messaging between donors and patients"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        # Users see messages they sent or received
        return Message.objects.filter(
            models.Q(sender=user) | models.Q(recipient=user)
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        message = serializer.save(sender=self.request.user)
        
        # Send notification to recipient
        NotificationService.notify_custom(
            message.recipient,
            f"New message from {message.sender.username}",
            message.content[:100],
            notification_type='system'
        )
    
    @action(detail=False, methods=['get'])
    def conversation(self, request):
        """Get conversation with a specific user"""
        other_user_id = request.query_params.get('user_id')
        sos_request_id = request.query_params.get('sos_request_id')
        
        if not other_user_id:
            return Response({'detail': 'user_id required'}, status=400)
        
        queryset = Message.objects.filter(
            (models.Q(sender=request.user, recipient_id=other_user_id) |
             models.Q(sender_id=other_user_id, recipient=request.user))
        )
        
        if sos_request_id:
            queryset = queryset.filter(sos_request_id=sos_request_id)
        
        messages = queryset.order_by('created_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark message as read"""
        message = self.get_object()
        if message.recipient_id != request.user.id:
            return Response({'detail': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        
        message.mark_as_read()
        return Response(self.get_serializer(message).data)


class EmergencyContactViewSet(viewsets.ModelViewSet):
    """Emergency contacts management"""
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users see their own emergency contacts
        return EmergencyContact.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
