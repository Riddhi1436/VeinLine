"""
Test the appointment booking flow using manage.py shell
"""
from django.contrib.auth.models import User
from accounts.models import Profile
from appointments.models import AppointmentSlot, Appointment
import json

def run_test():
    print("\n" + "="*60)
    print("TESTING APPOINTMENT BOOKING SYSTEM")
    print("="*60)
    
    # 1. Check available slots
    print("\n1. Checking available slots...")
    slots = AppointmentSlot.objects.filter(status='available')[:1]
    if slots:
        slot = slots[0]
        print(f"   ✓ Found slots: {slots.count()} total available")
        print(f"     Sample: {slot.blood_bank} in {slot.city} on {slot.date}")
        slot_id = slot.id
    else:
        print("   ✗ No available slots found")
        return
    
    # 2. Check test user and create if needed
    print("\n2. Setting up test user...")
    user = User.objects.filter(username='testdonor2').first()
    if not user:
        user = User.objects.create_user(
            username='testdonor2',
            email='testdonor2@example.com',
            password='testpass123'
        )
        Profile.objects.get_or_create(user=user, defaults={'role': 'donor'})
        print(f"   ✓ Created test user: testdonor2")
    else:
        print(f"   ✓ Using existing user: testdonor2")
    
    # 3. Try to book an appointment
    print("\n3. Booking appointment...")
    try:
        appointment = Appointment.objects.create(
            donor=user,
            slot=slot,
            status='pending'
        )
        print(f"   ✓ Appointment created")
        print(f"     ID: {appointment.id}")
        print(f"     Status: {appointment.status}")
        print(f"     Slot: {slot.blood_bank}")
        appointment_id = appointment.id
    except Exception as e:
        print(f"   ✗ Failed to book: {str(e)}")
        return
    
    # 4. Check appointment in DB
    print("\n4. Verifying appointment...")
    try:
        apt = Appointment.objects.get(id=appointment_id)
        print(f"   ✓ Appointment verified in database")
        print(f"     Donor: {apt.donor.username}")
        print(f"     Has health questionnaire: {apt.health_questionnaire is not None}")
    except Appointment.DoesNotExist:
        print(f"   ✗ Appointment not found")
        return
    
    # 5. Check user's appointments
    print("\n5. Checking user appointments...")
    user_appointments = Appointment.objects.filter(donor=user)
    print(f"   ✓ Found {user_appointments.count()} appointment(s) for user")
    
    print("\n" + "="*60)
    print("✓ BASIC APPOINTMENT SYSTEM WORKING")
    print("="*60 + "\n")

if __name__ == '__main__':
    run_test()
