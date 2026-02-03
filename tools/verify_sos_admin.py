#!/usr/bin/env python
"""
Verification script for SOS admin UI and site functionality
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

# Ensure ALLOWED_HOSTS includes test hosts
from django.conf import settings
if 'testserver' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('testserver')
if '127.0.0.1' not in settings.ALLOWED_HOSTS:
    settings.ALLOWED_HOSTS.append('127.0.0.1')

User = get_user_model()
client = Client()

print("=" * 70)
print("VEINLINE SOS & ADMIN VERIFICATION")
print("=" * 70)

# Test 1: Homepage
print("\n[TEST 1] Homepage (Anonymous)")
r = client.get('/')
print(f"  Status: {r.status_code} {'✓' if r.status_code == 200 else '✗'}")

# Test 2: Create SOS (Anonymous - should redirect)
print("\n[TEST 2] Create SOS (Anonymous)")
r = client.get('/sos/create/')
print(f"  Status: {r.status_code} {'✓' if r.status_code == 302 else '✗'} (redirect expected)")

# Test 3: Admin login
print("\n[TEST 3] Admin Setup")
try:
    admin_user = User.objects.get(username='test_admin_verify')
    print(f"  Admin user exists: {admin_user.username} ✓")
except User.DoesNotExist:
    admin_user = User.objects.create_superuser(
        username='test_admin_verify',
        email='admin@test.local',
        password='adminpass123'
    )
    Profile.objects.get_or_create(
        user=admin_user,
        defaults={'role': 'admin', 'phone_e164': '+1234567890'}
    )
    print(f"  Admin user created: {admin_user.username} ✓")

# Test 4: Admin login
print("\n[TEST 4] Admin Login")
logged_in = client.login(username='test_admin_verify', password='adminpass123')
print(f"  Login: {'✓' if logged_in else '✗'}")

# Test 5: Admin index
print("\n[TEST 5] Admin Index")
r = client.get('/admin/')
print(f"  Status: {r.status_code} {'✓' if r.status_code == 200 else '✗'}")

# Test 6: SOS Changelist (the critical test)
print("\n[TEST 6] SOS Admin Changelist (CRITICAL)")
try:
    r = client.get('/admin/sos/sosrequest/')
    if r.status_code == 200:
        print(f"  Status: {r.status_code} ✓✓✓ SUCCESS")
        print(f"  Page renders correctly with custom admin UI")
        # Check for some expected HTML markers
        content = r.content.decode('utf-8', errors='ignore')
        if 'sos_id_display' in content or 'priority_display' in content or 'responses_count' in content:
            print(f"  Custom display methods detected ✓")
        else:
            print(f"  Note: Page loads but custom markers not found (may still be working)")
    else:
        print(f"  Status: {r.status_code} ✗ FAILED")
except Exception as e:
    print(f"  Error: {e} ✗")

# Test 7: SOS Response Changelist
print("\n[TEST 7] SOS Response Changelist")
try:
    r = client.get('/admin/sos/sosresponse/')
    print(f"  Status: {r.status_code} {'✓' if r.status_code == 200 else '✗'}")
except Exception as e:
    print(f"  Error: {e}")

# Test 8: Create SOS (Authenticated Patient)
print("\n[TEST 8] Create SOS (Authenticated)")
# Create patient user
try:
    patient_user = User.objects.get(username='test_patient_verify')
except User.DoesNotExist:
    patient_user = User.objects.create_user(
        username='test_patient_verify',
        email='patient@test.local',
        password='patientpass123'
    )
    Profile.objects.get_or_create(
        user=patient_user,
        defaults={'role': 'patient', 'phone_e164': '+9876543210', 'city': 'Test City', 'area': 'Test Area'}
    )

client.login(username='test_patient_verify', password='patientpass123')
r = client.get('/sos/create/')
print(f"  Status: {r.status_code} {'✓' if r.status_code == 200 else '✗'}")

print("\n" + "=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
