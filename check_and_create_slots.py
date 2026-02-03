#!/usr/bin/env python
import os
import sys
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from appointments.models import AppointmentSlot
from core.constants import SUPPORTED_CITIES

# Check existing slots
total_slots = AppointmentSlot.objects.count()
print(f"Current total slots: {total_slots}")

if total_slots == 0:
    print("\n⚠️  No slots found. Creating sample data...\n")
    
    # Create sample slots for next 30 days
    cities = SUPPORTED_CITIES
    blood_banks = [
        ('red_crescent', 'Red Crescent Blood Bank'),
        ('city_hospital', 'City Hospital Blood Bank'),
        ('private_clinic', 'Private Clinic Blood Bank'),
        ('mobile_unit', 'Mobile Donation Unit'),
    ]
    
    slots_created = 0
    base_date = datetime.now().date()
    
    for day_offset in range(1, 15):  # Create slots for next 14 days
        slot_date = base_date + timedelta(days=day_offset)
        
        for city in cities:
            for blood_bank_code, blood_bank_name in blood_banks:
                # Create 2 slots per day per city/bank (morning and afternoon)
                for hour in [9, 14]:  # 9 AM and 2 PM
                    slot = AppointmentSlot.objects.create(
                        blood_bank=blood_bank_code,
                        city=city,
                        address=f"{blood_bank_name} - {city}",
                        date=slot_date,
                        start_time=f"{hour:02d}:00",
                        end_time=f"{hour+2:02d}:00",
                        max_donors=15,
                        booked_donors=0,
                        status='available',
                        notes=f"Donation session from {hour:02d}:00 to {hour+2:02d}:00"
                    )
                    slots_created += 1
    
    print(f"✅ Created {slots_created} appointment slots")
    print(f"📊 Total slots now: {AppointmentSlot.objects.count()}")
    
    # Show samples
    print("\n📋 Sample slots created:")
    for slot in AppointmentSlot.objects.all()[:5]:
        print(f"  - {slot.blood_bank} in {slot.city} on {slot.date} at {slot.start_time}")
else:
    print(f"✅ Found {total_slots} slots already in database")
    print("\n📋 Sample slots:")
    for slot in AppointmentSlot.objects.all()[:5]:
        print(f"  - {slot.blood_bank} in {slot.city} on {slot.date} at {slot.start_time} ({slot.remaining_slots()} spots)")
