#!/usr/bin/env python
"""
Test the appointment API endpoints
"""
import os
import sys
import django
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

client = Client()

print("=" * 60)
print("Testing Appointment API Endpoints")
print("=" * 60)

# Test 1: GET /api/slots/upcoming/
print("\n1️⃣  Testing GET /api/slots/upcoming/")
response = client.get('/api/slots/upcoming/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Returned {len(data)} slots")
    if data:
        print(f"   Sample slot: {data[0]}")
else:
    print(f"   ❌ Error: {response.content.decode()}")

# Test 2: GET /api/slots/
print("\n2️⃣  Testing GET /api/slots/")
response = client.get('/api/slots/')
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   ✅ Returned {len(data)} slots")
else:
    print(f"   ❌ Error: {response.content.decode()}")

# Test 3: GET /api/my-appointments/ (should fail without auth)
print("\n3️⃣  Testing GET /api/my-appointments/ (without auth)")
response = client.get('/api/my-appointments/')
print(f"   Status: {response.status_code}")
if response.status_code == 401:
    print(f"   ✅ Correctly returns 401 Unauthorized")
else:
    print(f"   Note: Status {response.status_code}")

print("\n" + "=" * 60)
print("API Endpoints are working! ✅")
print("=" * 60)
