#!/usr/bin/env python
"""
Test SOS edit/change form rendering
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))
os.chdir(str(project_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from accounts.models import Profile
from sos.models import SOSRequest

# Ensure ALLOWED_HOSTS includes test hosts
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')

User = get_user_model()
client = Client()

print("=" * 70)
print("SOS ADMIN CHANGE FORM TEST")
print("=" * 70)

# Setup admin
try:
    admin_user = User.objects.get(username='test_admin_change_form')
except User.DoesNotExist:
    admin_user = User.objects.create_superuser(
        username='test_admin_change_form',
        email='admin@test.local',
        password='adminpass123'
    )
    Profile.objects.get_or_create(
        user=admin_user,
        defaults={'role': 'admin', 'phone_e164': '+1234567890'}
    )

# Login
print("\n[1] Admin Login")
logged_in = client.login(username='test_admin_change_form', password='adminpass123')
print(f"  Status: {'✓' if logged_in else '✗'}")

# Create a test SOS request
print("\n[2] Creating Test SOS Request")
try:
    patient_user = User.objects.get(username='test_patient_sos_form')
except User.DoesNotExist:
    patient_user = User.objects.create_user(
        username='test_patient_sos_form',
        email='patient@test.local',
        password='patientpass123'
    )
    Profile.objects.get_or_create(
        user=patient_user,
        defaults={'role': 'patient', 'phone_e164': '+9876543210', 'city': 'Test City', 'area': 'Test Area'}
    )

sos = SOSRequest.objects.create(
    requester=patient_user,
    blood_group_needed='O+',
    units_needed=2,
    city='Test City',
    area='Test Area',
    hospital_name='Test Hospital',
    message='Emergency blood needed',
    priority='critical'
)
print(f"  Created SOS #{sos.id} ✓")

# Test changelist
print("\n[3] Admin Changelist")
r = client.get('/admin/sos/sosrequest/')
print(f"  Status: {r.status_code} {'✓' if r.status_code == 200 else '✗'}")

# Test change form (THE CRITICAL TEST)
print("\n[4] Admin Change Form (CRITICAL)")
try:
    r = client.get(f'/admin/sos/sosrequest/{sos.id}/change/')
    if r.status_code == 200:
        print(f"  Status: {r.status_code} ✓✓✓ SUCCESS")
        print(f"  Change form renders correctly!")
    else:
        print(f"  Status: {r.status_code} ✗ FAILED")
except Exception as e:
    print(f"  Error: {e} ✗")

print("\n" + "=" * 70)
print("TEST COMPLETE")
print("=" * 70)
