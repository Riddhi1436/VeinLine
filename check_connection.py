#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from accounts.models import Profile
from donations.models import DonorDetails
from sos.models import SOSRequest, SOSResponse, DonationTracker

User = get_user_model()

print("=" * 60)
print("DATABASE STATE CHECK")
print("=" * 60)

print(f"\nTotal Users: {User.objects.count()}")
print(f"Total Profiles: {Profile.objects.count()}")
print(f"Total DonorDetails: {DonorDetails.objects.count()}")
print(f"Total SOS Requests: {SOSRequest.objects.count()}")
print(f"Total SOS Responses: {SOSResponse.objects.count()}")
print(f"Total DonationTrackers: {DonationTracker.objects.count()}")

print("\n" + "=" * 60)
print("CHECKING SOS CONNECTIONS")
print("=" * 60)

# Check all SOS requests
sos_requests = SOSRequest.objects.all()
print(f"\nFound {sos_requests.count()} SOS Requests:")
for sos_req in sos_requests:
    print(f"\n  SOS Request #{sos_req.id}:")
    print(f"    Requester: {sos_req.requester.username} (ID: {sos_req.requester_id})")
    print(f"    Blood Group: {sos_req.blood_group_needed}")
    print(f"    City: {sos_req.city}")
    print(f"    Status: {sos_req.status}")
    print(f"    Priority: {sos_req.priority}")
    
    # Check responses
    responses = sos_req.responses.all()
    print(f"    Responses: {responses.count()}")
    for resp in responses:
        print(f"      - Donor: {resp.donor.username} (ID: {resp.donor_id})")
        print(f"        Response: {resp.response}")
        print(f"        Channel: {resp.channel}")
        print(f"        Consented: {resp.donor_consented_to_share_contact}")
        print(f"        Responded At: {resp.responded_at}")
        
        # Check if donation tracker exists
        tracker = resp.donation_tracker
        if tracker:
            print(f"        Tracker Status: {tracker.current_status}")
        else:
            print(f"        Tracker: None")

print("\n" + "=" * 60)
print("CONNECTION VERIFICATION")
print("=" * 60)

# Verify all connections
all_good = True
for sos_req in sos_requests:
    for resp in sos_req.responses.all():
        # Check patient (requester) can access response
        if resp.request.requester_id != sos_req.requester_id:
            print(f"❌ SOS Request {sos_req.id} - Response {resp.id}: Patient mismatch!")
            all_good = False
        
        # Check donor connection
        if resp.donor_id is None:
            print(f"❌ SOS Request {sos_req.id} - Response {resp.id}: Donor missing!")
            all_good = False

if all_good:
    print("✅ All connections are valid!")
else:
    print("❌ Some connections are broken!")

print("\n" + "=" * 60)
