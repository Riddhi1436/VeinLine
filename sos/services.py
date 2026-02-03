from __future__ import annotations

from django.conf import settings
from django.db.models import Q

from core.models import BloodGroupCompatibility
from donations.models import DonorDetails


DEFAULT_COMPATIBILITY = {
    # Recipient -> allowed donor groups
    "O-": {"O-"},
    "O+": {"O-", "O+"},
    "A-": {"O-", "A-"},
    "A+": {"O-", "O+", "A-", "A+"},
    "B-": {"O-", "B-"},
    "B+": {"O-", "O+", "B-", "B+"},
    "AB-": {"O-", "A-", "B-", "AB-"},
    "AB+": {"O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"},
}


def compatible_donor_groups(recipient_group: str) -> set[str]:
    qs = BloodGroupCompatibility.objects.filter(recipient_group=recipient_group, is_compatible=True).values_list(
        "donor_group", flat=True
    )
    donor_groups = set(qs)
    if donor_groups:
        return donor_groups
    return DEFAULT_COMPATIBILITY.get(recipient_group, set())


def match_donors_for_request(sos_request, limit: int = 50):
    """
    Rule-based matching:
    - Compatible blood group
    - Same city (strict by default; configurable)
    - Availability status
    """

    groups = compatible_donor_groups(sos_request.blood_group_needed)
    if not groups:
        return DonorDetails.objects.none()

    q = Q(blood_group__in=groups) & Q(is_available=True)

    if getattr(settings, "VEINLINE_CITY_MATCH_STRICT", True):
        q &= Q(city__iexact=sos_request.city)
        if sos_request.area:
            # Area is optional; if present we prefer donors in same area but don't require it.
            q &= Q(city__iexact=sos_request.city)
    else:
        # Non-strict: allow same city OR blank donor city for rural/offline data.
        q &= Q(city__iexact=sos_request.city) | Q(city="")

    qs = DonorDetails.objects.filter(q).select_related("user").order_by("-updated_at")
    return qs[:limit]


