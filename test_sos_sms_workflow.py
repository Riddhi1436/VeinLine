"""
SOS SMS Workflow Test Script
This script tests the complete SOS to SMS workflow:
1. Creates test patient and donor users
2. Creates donor details with phone numbers
3. Creates an SOS request
4. Tests SMS sending
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import Profile, UserRole
from donations.models import DonorDetails, DonorStatistics
from sos.models import SOSRequest, SOSStatus, SOSPriority, SOSResponse, ResponseChoice, ResponseChannel
from sos.services import match_donors_for_request
from core.services.sms import send_sms

User = get_user_model()

print("=" * 70)
print("VeinLine SOS SMS Workflow Test")
print("=" * 70)

# Step 1: Create test patient user
print("\n[1] Creating test patient user...")
patient_user, created = User.objects.get_or_create(
    username='test_patient_sms',
    defaults={
        'email': 'patient@test.com',
        'first_name': 'Test',
        'last_name': 'Patient',
    }
)
if created:
    patient_user.set_password('testpass123')
    patient_user.save()
    print(f"✓ Created patient user: {patient_user.username}")
else:
    print(f"✓ Using existing patient user: {patient_user.username}")

# Ensure patient profile
patient_profile, _ = Profile.objects.get_or_create(
    user=patient_user,
    defaults={
        'role': UserRole.PATIENT,
        'city': 'Bangalore',
        'phone_e164': '+919000000001',
    }
)
print(f"✓ Patient profile: {patient_profile.role} in {patient_profile.city}")

# Step 2: Create test donor users with phone numbers
print("\n[2] Creating test donor users...")
donors_data = [
    {
        'username': 'test_donor_1',
        'email': 'donor1@test.com',
        'full_name': 'Donor One',
        'phone': '+919000000101',
    },
    {
        'username': 'test_donor_2',
        'email': 'donor2@test.com',
        'full_name': 'Donor Two',
        'phone': '+919000000102',
    },
    {
        'username': 'test_donor_3',
        'email': 'donor3@test.com',
        'full_name': 'Donor Three',
        'phone': '+919000000103',
    },
]

donor_users = []
for donor_data in donors_data:
    user, created = User.objects.get_or_create(
        username=donor_data['username'],
        defaults={
            'email': donor_data['email'],
            'first_name': donor_data['full_name'].split()[0],
            'last_name': donor_data['full_name'].split()[-1],
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"  ✓ Created donor user: {user.username}")
    else:
        print(f"  ✓ Using existing donor user: {user.username}")
    
    donor_users.append(user)
    
    # Ensure donor profile
    profile, _ = Profile.objects.get_or_create(
        user=user,
        defaults={
            'role': UserRole.DONOR,
            'city': 'Bangalore',
            'phone_e164': donor_data['phone'],
        }
    )
    
    # Ensure donor details
    details, _ = DonorDetails.objects.get_or_create(
        user=user,
        defaults={
            'full_name': donor_data['full_name'],
            'age': 25,
            'blood_group': 'O+',
            'city': 'Bangalore',
            'is_available': True,
        }
    )
    
    # Ensure donor statistics
    stats, _ = DonorStatistics.objects.get_or_create(
        donor=user,
        defaults={
            'total_donations': 0,
            'sos_responses': 0,
        }
    )
    
    print(f"  ✓ Donor profile: {profile.phone_e164}")

# Step 3: Create SOS request
print("\n[3] Creating SOS request...")
sos_req = SOSRequest.objects.create(
    requester=patient_user,
    blood_group_needed='O+',
    units_needed=2,
    city='Bangalore',
    area='Indiranagar',
    hospital_name='Apollo Hospital',
    message='Emergency blood needed for surgery',
    status=SOSStatus.OPEN,
    priority=SOSPriority.URGENT,
)
print(f"✓ SOS Request created: #{sos_req.id}")
print(f"  Blood Group: {sos_req.blood_group_needed}")
print(f"  Units: {sos_req.units_needed}")
print(f"  Priority: {sos_req.priority}")
print(f"  SMS Token: {sos_req.sms_reply_token}")

# Step 4: Find matching donors
print("\n[4] Finding matching donors...")
matched_donors = match_donors_for_request(sos_req, limit=50)
matched_list = list(matched_donors)
print(f"✓ Found {len(matched_list)} matching donors")

# Step 5: Create SOSResponse records
print("\n[5] Creating SOSResponse records...")
for donor in matched_list:
    resp, created = SOSResponse.objects.get_or_create(
        request=sos_req,
        donor=donor.user,
        defaults={
            'response': ResponseChoice.PENDING,
            'channel': ResponseChannel.SMS,
        }
    )
    status_text = "Created" if created else "Already exists"
    print(f"  ✓ SOSResponse {status_text}: donor={donor.user.username}, response_id={resp.id}")

# Step 6: Send SMS to donors
print("\n[6] Sending SMS to matching donors...")
print(f"Note: SMS_API_KEY must be configured in .env to send real SMS")
print("-" * 70)

sms_message = (
    f"VeinLine SOS: Need {sos_req.blood_group_needed} blood in {sos_req.city}. "
    f"Reply: YES {sos_req.sms_reply_token} or NO {sos_req.sms_reply_token}."
)

sms_success = 0
sms_skipped = 0
sms_failed = 0

for donor in matched_list:
    phone = getattr(getattr(donor.user, 'profile', None), 'phone_e164', '')
    
    if not phone:
        print(f"  ⚠ {donor.full_name}: No phone number")
        sms_skipped += 1
        continue
    
    print(f"\n  Sending to {donor.full_name} ({phone})...")
    try:
        result = send_sms(phone, sms_message)
        if result.get('ok'):
            if not result.get('skipped'):
                print(f"    ✓ SMS sent successfully")
                sms_success += 1
            else:
                print(f"    ⚠ SMS skipped: {result.get('reason', 'unknown reason')}")
                sms_skipped += 1
        else:
            print(f"    ✗ SMS failed: {result.get('reason', 'unknown error')}")
            sms_failed += 1
    except Exception as e:
        print(f"    ✗ Exception: {str(e)}")
        sms_failed += 1

# Step 7: Print summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"Patient User: {patient_user.username}")
print(f"Donor Users Created: {len(donor_users)}")
print(f"SOS Request: #{sos_req.id} ({sos_req.blood_group_needed} in {sos_req.city})")
print(f"Matching Donors Found: {len(matched_list)}")
print(f"SOSResponse Records Created: {len(matched_list)}")
print(f"\nSMS Statistics:")
print(f"  ✓ Sent: {sms_success}")
print(f"  ⚠ Skipped: {sms_skipped}")
print(f"  ✗ Failed: {sms_failed}")

if sms_skipped > 0:
    print(f"\n⚠ Note: SMS skipped likely means SMS_API_KEY is not configured.")
    print(f"   Set SMS_API_KEY in .env to enable actual SMS sending.")

print("\n✓ Test workflow completed successfully!")
print("=" * 70)
