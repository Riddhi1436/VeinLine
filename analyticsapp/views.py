from django.db.models import Count, Sum
from rest_framework import permissions, views
from rest_framework.response import Response

from donations.models import BloodBankInventory, DonorDetails
from sos.models import SOSRequest, SOSResponse


class AdminAnalyticsView(views.APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        donors_by_group = (
            DonorDetails.objects.values("blood_group").annotate(count=Count("id")).order_by("blood_group")
        )
        donors_active = DonorDetails.objects.filter(is_available=True).count()
        donors_inactive = DonorDetails.objects.filter(is_available=False).count()

        shortages = (
            BloodBankInventory.objects.values("blood_group")
            .annotate(units=Sum("units_available"))
            .order_by("blood_group")
        )

        sos_stats = SOSRequest.objects.values("status").annotate(count=Count("id")).order_by("status")
        response_stats = SOSResponse.objects.values("response").annotate(count=Count("id")).order_by("response")

        return Response(
            {
                "donors_by_group": list(donors_by_group),
                "donors_activity": {"active": donors_active, "inactive": donors_inactive},
                "sos_by_status": list(sos_stats),
                "responses_by_choice": list(response_stats),
                "inventory_records_by_group": list(shortages),
            }
        )

from django.shortcuts import render

# Create your views here.
