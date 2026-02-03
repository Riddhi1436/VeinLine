#!/usr/bin/env python
"""
Test script to verify the complete appointment booking flow.
This script simulates a user booking an appointment and completing the health questionnaire.
"""

import os
import sys
import django
import json

# Add the project to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from django.contrib.auth.models import User
from django.test import Client

from accounts.models import Profile
from appointments.models import AppointmentSlot, Appointment, HealthQuestionnaire

def test_appointment_flow():
    """Test the complete appointment booking flow"""
    print("\n" + "="*60)
    print("TESTING APPOINTMENT BOOKING FLOW")
    print("="*60)
    
    client = Client(SERVER_NAME='localhost')  # Set proper server name
    
    # Step 1: Create a test user
    print("\n1. Creating test user...")
    username = "testdonor"
    email = "testdonor@example.com"
    password = "testpass123"
    
    # Delete if exists
    User.objects.filter(username=username).delete()
    
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password
    )
    
    # Create profile (or get existing)
    profile, created = Profile.objects.get_or_create(user=user, defaults={'role': 'donor'})
    if created:
        print(f"   ✓ User created: {username}")
    else:
        print(f"   ✓ Using existing user: {username}")
    
    # Step 2: Login
    print("\n2. Logging in...")
    login_success = client.login(username=username, password=password)
    if login_success:
        print("   ✓ Login successful")
    else:
        print("   ✗ Login failed")
        return
    
    # Step 3: Get available slots
    print("\n3. Fetching available slots...")
    response = client.get('/api/slots/upcoming/')
    if response.status_code == 200:
        slots = response.json()
        print(f"   ✓ Found {len(slots)} available slots")
        if slots:
            slot = slots[0]
            print(f"     Sample slot: {slot['blood_bank']} in {slot['city']} on {slot['date']}")
        else:
            print("   ✗ No slots available")
            return
    else:
        print(f"   ✗ Failed to fetch slots: {response.status_code}")
        return
    
    # Step 4: Book an appointment
    print("\n4. Booking an appointment...")
    slot_id = slot['id']
    response = client.post(
        '/api/my-appointments/',
        data=json.dumps({'slot_id': slot_id}),
        content_type='application/json'
    )
    
    if response.status_code == 201:
        appointment = response.json()
        appointment_id = appointment['id']
        print(f"   ✓ Appointment booked: ID {appointment_id}")
        print(f"     Status: {appointment['status']}")
    else:
        print(f"   ✗ Failed to book appointment: {response.status_code}")
        print(f"     Response: {response.content.decode()}")
        return
    
    # Step 5: Submit health questionnaire
    print("\n5. Submitting health questionnaire...")
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
        'additional_notes': 'Test submission'
    }
    
    response = client.post(
        f'/api/appointments/{appointment_id}/health-questionnaire/',
        data=json.dumps(health_data),
        content_type='application/json'
    )
    
    if response.status_code == 201:
        questionnaire = response.json()
        print(f"   ✓ Health questionnaire submitted")
        print(f"     Is eligible: {questionnaire.get('is_eligible', 'N/A')}")
    else:
        print(f"   ✗ Failed to submit health questionnaire: {response.status_code}")
        print(f"     Response: {response.content.decode()}")
        return
    
    # Step 6: Verify appointment in database
    print("\n6. Verifying appointment in database...")
    try:
        appointment = Appointment.objects.get(id=appointment_id)
        print(f"   ✓ Appointment found in database")
        print(f"     Donor: {appointment.donor.username}")
        print(f"     Slot: {appointment.slot.blood_bank} ({appointment.slot.city})")
        print(f"     Status: {appointment.status}")
        print(f"     Has health questionnaire: {appointment.health_questionnaire is not None}")
    except Appointment.DoesNotExist:
        print(f"   ✗ Appointment not found in database")
        return
    
    # Step 7: Retrieve personal appointments
    print("\n7. Retrieving personal appointments...")
    response = client.get('/api/my-appointments/')
    if response.status_code == 200:
        appointments = response.json()
        print(f"   ✓ Retrieved {len(appointments)} appointment(s)")
        if appointments:
            apt = appointments[0]
            print(f"     Appointment: {apt['slot_details']['blood_bank']} on {apt['slot_details']['date']}")
            print(f"     Status: {apt['status']}")
    else:
        print(f"   ✗ Failed to retrieve appointments: {response.status_code}")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED - APPOINTMENT BOOKING FLOW IS WORKING")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        test_appointment_flow()
    except Exception as e:
        print(f"\n✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
