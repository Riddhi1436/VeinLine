#!/usr/bin/env python
"""
Script to create sample appointment slots for testing
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from appointments.models import AppointmentSlot
from core.constants import SUPPORTED_CITIES
from datetime import datetime, timedelta
from django.utils import timezone

# Delhi NCR and Uttar Pradesh (from core.constants)
cities = SUPPORTED_CITIES
blood_bank_choices = ['red_crescent', 'city_hospital', 'private_clinic', 'mobile_unit']
bank_names = {
    'red_crescent': 'Red Crescent Blood Bank',
    'city_hospital': 'City Hospital Blood Bank',
    'private_clinic': 'Private Clinic Blood Bank',
    'mobile_unit': 'Mobile Donation Unit'
}

# Clear existing slots
AppointmentSlot.objects.all().delete()

# Create slots for next 30 days
start_date = timezone.now().date()
slot_count = 0

for day_offset in range(30):
    appointment_date = start_date + timedelta(days=day_offset)
    
    # Skip Sundays
    if appointment_date.weekday() == 6:
        continue
    
    for city in cities:
        for bank_choice in blood_bank_choices:
            # Create 2 slots per day per city per bank (10:00 AM, 3:00 PM)
            times = [
                ('10:00', '11:00'),
                ('15:00', '16:00'),
            ]
            
            for start_time_str, end_time_str in times:
                # Convert string times to time objects
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                
                slot = AppointmentSlot.objects.create(
                    city=city,
                    blood_bank=bank_choice,
                    date=appointment_date,
                    start_time=start_time,
                    end_time=end_time,
                    max_donors=5,
                    booked_donors=0,
                    status='available',
                    address=f'{city} Medical Center'
                )
                slot_count += 1

print(f"✅ Created {slot_count} appointment slots!")
print(f"Sample slots available for Delhi NCR & Uttar Pradesh: {', '.join(cities)}")
