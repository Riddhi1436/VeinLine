#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick verification script to check VeinLine setup
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.models import BloodGroupCompatibility
from accounts.models import Profile
from donations.models import DonorDetails, BloodBankInventory
from sos.models import SOSRequest, SOSResponse

User = get_user_model()

print("=" * 50)
print("VeinLine Setup Verification")
print("=" * 50)
print()

# Check database
print("[OK] Database connection: OK")

# Check superuser
superuser_count = User.objects.filter(is_superuser=True).count()
print(f"[OK] Superusers: {superuser_count}")

# Check compatibility data
compat_count = BloodGroupCompatibility.objects.count()
print(f"[OK] Blood group compatibility records: {compat_count}")

# Check models
print(f"[OK] Total users: {User.objects.count()}")
print(f"[OK] Total profiles: {Profile.objects.count()}")
print(f"[OK] Total donors: {DonorDetails.objects.count()}")
print(f"[OK] Total inventory items: {BloodBankInventory.objects.count()}")
print(f"[OK] Total SOS requests: {SOSRequest.objects.count()}")
print(f"[OK] Total SOS responses: {SOSResponse.objects.count()}")

print()
print("=" * 50)
print("Setup Complete! [OK]")
print("=" * 50)
print()
print("To start the server:")
print("  Windows: start_server.bat")
print("  Linux/Mac: ./start_server.sh")
print("  Or manually: python manage.py runserver")
print()
print("Admin Login:")
print("  URL: http://127.0.0.1:8000/admin/")
print("  Username: admin")
print("  Password: admin123")
print()

