"""
Test SOS match endpoint via HTTP API with JWT
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')

import django
django.setup()

from django.contrib.auth.models import User
from django.conf import settings
from donations.models import DonorDetails
from sos.models import SOSRequest
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

# Add testserver to ALLOWED_HOSTS temporarily for testing
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + ['testserver']

print("=" * 70)
print("SOS MATCH API ENDPOINT TEST")
print("=" * 70)

# Clean up old test data
User.objects.filter(username__startswith='test_api_').delete()
print("\n✓ Cleaned up old test data")

client = APIClient()

# Step 1: Create test donor
print("\n[Step 1] Creating test donor...")
donor = User.objects.create_user(
    username='test_api_donor_1',
    email='apidoner@test.com',
    password='test123'
)
donor_profile = donor.profile
donor_profile.role = 'donor'
donor_profile.save()
DonorDetails.objects.create(
    user=donor,
    blood_group='O+',
    age=25,
    city='Mumbai',
    is_available=True
)
print(f"✓ Donor created: {donor.username}")

# Step 2: Create patient and get JWT token
print("\n[Step 2] Creating patient and getting JWT token...")
patient = User.objects.create_user(
    username='test_api_patient_1',
    email='apipatient@test.com',
    password='test123'
)
patient_profile = patient.profile
patient_profile.role = 'patient'
patient_profile.save()

# Get JWT token
refresh = RefreshToken.for_user(patient)
token = str(refresh.access_token)
print(f"✓ Patient created: {patient.username}")
print(f"✓ JWT token obtained")

client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

# Step 3: Create SOS request
print("\n[Step 3] Creating SOS request via API...")
sos_data = {
    'blood_group_needed': 'O+',
    'city': 'Mumbai',
    'priority': 'urgent',
    'units_needed': 2
}
response = client.post('/api/sos/requests/', sos_data, format='json')
if response.status_code != 201:
    print(f"✗ SOS creation failed: {response.status_code}")
    print(f"  Response: {response.json()}")
else:
    sos_data_response = response.json()
    sos_id = sos_data_response['id']
    print(f"✓ SOS request created via API")
    print(f"  - ID: {sos_id}")
    print(f"  - Blood: {sos_data_response['blood_group_needed']}")
    print(f"  - City: {sos_data_response['city']}")

# Step 4: Call the match endpoint
print("\n[Step 4] Calling /api/sos/requests/{id}/match/ endpoint...")
try:
    response = client.post(f'/api/sos/requests/{sos_id}/match/', format='json')
    print(f"Response status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 200:
        print(f"\n✓ Match endpoint SUCCEEDED!")
        print(f"\nResponse details:")
        print(f"  - Request ID: {result.get('request_id')}")
        print(f"  - Matched donors: {result.get('matched_donors', 0)}")
        print(f"  - Responses created: {len(result.get('responses_created_or_found', []))}")
        print(f"  - SMS results sent: {len(result.get('sms_results', []))}")
        
        if result.get('responses_created_or_found'):
            print(f"\n  Details of created responses:")
            for resp in result.get('responses_created_or_found', []):
                print(f"    - Donor ID: {resp.get('donor_id')}, Response ID: {resp.get('response_id')}, Created: {resp.get('created')}")
    else:
        print(f"\n✗ Match endpoint FAILED with status {response.status_code}")
        print(f"  Error: {result}")
        
except Exception as e:
    print(f"✗ Error calling endpoint: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("API ENDPOINT TEST COMPLETE")
print("=" * 70)
