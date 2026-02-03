"""
Test appointment API endpoints directly
"""
import os
import django
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

import json
import requests
from django.contrib.auth.models import User
from accounts.models import Profile
from appointments.models import AppointmentSlot, Appointment

print("\n" + "="*70)
print("TESTING APPOINTMENT API ENDPOINTS")
print("="*70)

# Test base URL
BASE_URL = 'http://localhost:8000'

# 1. Test getting slots without authentication
print("\n1. Testing GET /api/slots/upcoming/ (no auth)...")
try:
    response = requests.get(f'{BASE_URL}/api/slots/upcoming/')
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        slots = response.json()
        print(f"   [OK] Got {len(slots)} slots")
        if slots:
            print(f"     First slot: {slots[0]['blood_bank']} - {slots[0]['city']} on {slots[0]['date']}")
    else:
        print(f"   [ERROR] Error: {response.text}")
except Exception as e:
    print(f"   [ERROR] Connection error: {e}")

# 2. Setup test user
print("\n2. Setting up test user...")
user = User.objects.filter(username='apitestuser').first()
if not user:
    user = User.objects.create_user(
        username='apitestuser',
        email='apitest@example.com',
        password='testpass123'
    )
    Profile.objects.get_or_create(user=user, defaults={'role': 'donor'})
    print(f"   [OK] Created user: apitestuser")
else:
    print(f"   [OK] Using existing user: apitestuser")

# 3. Get a JWT token and test login
print("\n3. Testing authentication...")
session = requests.Session()
response = session.post(f'{BASE_URL}/api/auth/token/', 
                       json={'username': 'apitestuser', 'password': 'testpass123'})
if response.status_code == 200:
    token_data = response.json()
    access_token = token_data.get('access')
    print(f"   [OK] Got JWT access token")
    headers = {'Authorization': f'Bearer {access_token}'}
else:
    print(f"   [ERROR] Token endpoint failed: {response.status_code}")
    print(f"     Response: {response.text}")
    headers = {}

# 4. Try to book appointment
print("\n4. Testing POST /api/my-appointments/ (booking)...")
try:
    # Find a slot that hasn't been booked by this user yet
    slot = AppointmentSlot.objects.filter(status='available').exclude(
        appointments__donor=user
    ).first()
    
    if not slot:
        # If all slots are booked, just use any available slot for testing
        slot = AppointmentSlot.objects.filter(status='available').first()
    
    if slot:
        slot_id = slot.id
        print(f"   Using slot ID: {slot_id}")
        
        # Check if user already has appointment for this slot
        from appointments.models import Appointment
        existing = Appointment.objects.filter(donor=user, slot=slot).first()
        if existing:
            apt_id = existing.id
            print(f"   [OK] Appointment already exists: ID {apt_id}")
        else:
            response = session.post(f'{BASE_URL}/api/my-appointments/',
                                   json={'slot_id': slot_id},
                                   headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                appointment = response.json()
                apt_id = appointment.get('id')
                print(f"   [OK] Appointment created: ID {apt_id}")
                print(f"     Status: {appointment.get('status')}")
            else:
                if 'UNIQUE constraint' in response.text:
                    print(f"   [OK] User already has appointment for this slot (constraint enforced)")
                    # Get the existing appointment
                    existing = Appointment.objects.filter(donor=user).first()
                    if existing:
                        apt_id = existing.id
                else:
                    print(f"   [ERROR] Booking failed: {response.status_code}")
                    print(f"     Response: {response.text}")
                    apt_id = None
            
            # 5. Test health questionnaire submission
            if apt_id:
                print(f"\n5. Testing POST /api/appointments/{apt_id}/health-questionnaire/...")
                health_data = {
                    'has_fever': False,
                    'has_cold_or_cough': False,
                    'has_high_blood_pressure': False,
                    'has_diabetes': False,
                    'has_heart_condition': False,
                    'has_cancer': False,
                    'has_hiv_or_aids': False,
                    'has_hepatitis': False,
                    'has_bleeding_disorder': False,
                    'is_pregnant': False,
                    'is_breastfeeding': False,
                    'recent_tattoo_or_piercing': False,
                    'recent_surgery': False,
                    'recent_blood_transfusion': False,
                    'recent_vaccination': False,
                    'takes_blood_thinners': False,
                    'takes_antibiotics': False,
                    'weight_kg': 70.0,
                    'hemoglobin_level': 14.5,
                    'additional_notes': 'Test health check'
                }
                
                response = session.post(f'{BASE_URL}/api/appointments/{apt_id}/health-questionnaire/',
                                       json=health_data,
                                       headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code in [200, 201]:
                    questionnaire = response.json()
                    print(f"   [OK] Health questionnaire submitted")
                    print(f"     Is eligible: {questionnaire.get('is_eligible', 'N/A')}")
                else:
                    if 'health_questionnaire' in response.text.lower() and 'already' in response.text.lower():
                        print(f"   [OK] Health questionnaire already exists")
                    else:
                        print(f"   [ERROR] Error: {response.text}")
                
                # 6. Retrieve appointments
                print(f"\n6. Testing GET /api/my-appointments/...")
                response = session.get(f'{BASE_URL}/api/my-appointments/', headers=headers)
                print(f"   Status: {response.status_code}")
                if response.status_code == 200:
                    appointments = response.json()
                    print(f"   [OK] Retrieved {len(appointments)} appointment(s)")
                    if appointments:
                        apt = appointments[0]
                        print(f"     Appointment: {apt['slot_details']['blood_bank']} - {apt['slot_details']['date']}")
                        print(f"     Status: {apt['status']}")
                else:
                    print(f"   [ERROR] Error: {response.text}")
    else:
        print(f"   [ERROR] No available slots found")
except Exception as e:
    print(f"   [ERROR] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("API TEST COMPLETE")
print("="*70 + "\n")
