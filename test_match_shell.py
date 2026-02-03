"""
Test SOS matching directly using Django shell approach
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')

import django
django.setup()

from django.contrib.auth.models import User
from accounts.models import Profile
from donations.models import DonorDetails
from sos.models import SOSRequest
from sos.services import match_donors_for_request

print("=" * 70)
print("SOS MATCH ENGINE TEST")
print("=" * 70)

# Clean up test users
User.objects.filter(username__startswith='test_match_').delete()
print("\n✓ Cleaned up old test data")

# Step 1: Create test donor
print("\n[Step 1] Creating test donor with O+ blood in Mumbai...")
donor = User.objects.create_user(
    username='test_match_donor_1',
    email='donor1@test.com',
    password='test123'
)
# Profile auto-created by signal, just get it
profile = donor.profile
profile.role = 'donor'
profile.save()
donor_details = DonorDetails.objects.create(
    user=donor,
    blood_group='O+',
    age=25,
    city='Mumbai',
    is_available=True
)
print(f"✓ Created donor: {donor.username}")
print(f"  - Blood: {donor_details.blood_group}")
print(f"  - City: {donor_details.city}")
print(f"  - Available: {donor_details.is_available}")

# Step 2: Create another donor in different city
print("\n[Step 2] Creating second donor with AB+ blood in Delhi...")
donor2 = User.objects.create_user(
    username='test_match_donor_2',
    email='donor2@test.com',
    password='test123'
)
profile2 = donor2.profile
profile2.role = 'donor'
profile2.save()
donor_details2 = DonorDetails.objects.create(
    user=donor2,
    blood_group='AB+',
    age=30,
    city='Delhi',
    is_available=True
)
print(f"✓ Created donor: {donor2.username}")
print(f"  - Blood: {donor_details2.blood_group}")
print(f"  - City: {donor_details2.city}")

# Step 3: Create patient and SOS request
print("\n[Step 3] Creating SOS request for O+ in Mumbai...")
patient = User.objects.create_user(
    username='test_match_patient_1',
    email='patient1@test.com',
    password='test123'
)
patient_profile = patient.profile
patient_profile.role = 'patient'
patient_profile.save()

sos_request = SOSRequest.objects.create(
    requester=patient,
    blood_group_needed='O+',
    city='Mumbai',
    priority='urgent',
    units_needed=2
)
print(f"✓ Created SOS request:")
print(f"  - ID: {sos_request.id}")
print(f"  - Blood needed: {sos_request.blood_group_needed}")
print(f"  - City: {sos_request.city}")
print(f"  - Token: {sos_request.sms_reply_token}")

# Step 4: Test the match_donors_for_request function
print("\n[Step 4] Testing match_donors_for_request()...")
try:
    matched = match_donors_for_request(sos_request, limit=50)
    matched_list = list(matched)
    print(f"✓ Function executed successfully")
    print(f"  - Found {len(matched_list)} matching donors")
    
    if matched_list:
        for i, donor_details in enumerate(matched_list, 1):
            print(f"    [{i}] {donor_details.user.username} - {donor_details.blood_group} in {donor_details.city}")
    else:
        print(f"    ✗ WARNING: No donors matched (expected to find donor 1)")
        print(f"    \n    Debugging info:")
        all_donors = DonorDetails.objects.all()
        print(f"    - Total donors in DB: {all_donors.count()}")
        for d in all_donors:
            print(f"      • {d.user.username}: {d.blood_group}, {d.city}, available={d.is_available}")
    
except Exception as e:
    print(f"✗ Error in match function: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
