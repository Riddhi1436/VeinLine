#!/usr/bin/env python
"""
Debug script to check SOS SMS issues
Run: python manage.py shell < check_sms_debug.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

from django.conf import settings
from django.db.models import Count
from accounts.models import Profile, DonorDetails
from sos.models import SOSRequest
from core.services.sms import send_sms

print("\n" + "="*80)
print("VeinLine SOS SMS Debugging Check")
print("="*80 + "\n")

# 1. Check SMS Configuration
print("1️⃣  SMS CONFIGURATION CHECK")
print("-" * 80)
sms_api_key = getattr(settings, 'VEINLINE_SMS_API_KEY', None)
sms_provider = getattr(settings, 'VEINLINE_SMS_PROVIDER', 'fast2sms')
print(f"   VEINLINE_SMS_PROVIDER: {sms_provider}")
print(f"   VEINLINE_SMS_API_KEY:  {'✅ SET' if sms_api_key else '❌ NOT SET'}")
if not sms_api_key:
    print("\n   ⚠️  VEINLINE_SMS_API_KEY not configured! SMS won't work.")
    print("   Add VEINLINE_SMS_API_KEY to .env or settings.py")
print()

# 2. Check Donors with Phone Numbers
print("2️⃣  DONOR PHONE NUMBERS CHECK")
print("-" * 80)
total_users = Profile.objects.count()
users_with_phone = Profile.objects.filter(phone_e164__isnull=False).exclude(phone_e164='').count()
print(f"   Total users: {total_users}")
print(f"   Users with phone_e164: {users_with_phone}")

total_donors = DonorDetails.objects.count()
donors_with_phone = DonorDetails.objects.filter(user__profile__phone_e164__isnull=False).exclude(user__profile__phone_e164='').count()
available_donors = DonorDetails.objects.filter(is_available=True).count()
available_with_phone = DonorDetails.objects.filter(is_available=True, user__profile__phone_e164__isnull=False).exclude(user__profile__phone_e164='').count()

print(f"\n   Total donors: {total_donors}")
print(f"   Donors with phone: {donors_with_phone}")
print(f"   Available donors: {available_donors}")
print(f"   Available donors with phone: {available_with_phone}")

if total_donors == 0:
    print("\n   ⚠️  No donors exist! Create some donors first.")
elif donors_with_phone == 0:
    print("\n   ⚠️  No donors have phone numbers! Donors must have phone_e164.")
    print("   Have donors update their profile with phone number.")
elif available_with_phone == 0:
    print("\n   ⚠️  No available donors with phone! Make sure donors set is_available=True")
print()

# 3. Check Recent SOS Requests
print("3️⃣  RECENT SOS REQUESTS")
print("-" * 80)
sos_requests = SOSRequest.objects.order_by('-created_at')[:5]
if sos_requests:
    for sos in sos_requests:
        print(f"   SOS #{sos.id}: {sos.blood_group_needed} in {sos.city} (Status: {sos.status})")
        print(f"      Created: {sos.created_at} | Requester: {sos.requester.username}")
        # Count responses
        responses = sos.responses.all()
        print(f"      Responses: {responses.count()}")
        for resp in responses:
            print(f"         - {resp.donor.username}: {resp.response}")
else:
    print("   ℹ️  No SOS requests found")
print()

# 4. Test SMS Sending
print("4️⃣  SMS SENDING TEST")
print("-" * 80)
if not sms_api_key:
    print("   ❌ Cannot test SMS - API key not set")
else:
    test_phone = None
    # Find first donor with phone
    donor = DonorDetails.objects.filter(user__profile__phone_e164__isnull=False).exclude(user__profile__phone_e164='').first()
    if donor:
        test_phone = donor.user.profile.phone_e164
        print(f"   Testing with: {donor.user.username} ({test_phone})")
    else:
        print("   ⚠️  No donor with phone found for testing")
    
    if test_phone:
        try:
            test_msg = "Test SMS from VeinLine - If you received this, SMS is working!"
            print(f"   Sending test message: '{test_msg[:50]}...'")
            result = send_sms(test_phone, test_msg)
            
            print(f"   Result: {result}")
            if result.get('ok'):
                print("   ✅ SMS test SUCCESS!")
            else:
                print(f"   ❌ SMS test FAILED: {result.get('reason', 'Unknown error')}")
        except Exception as e:
            print(f"   ❌ SMS error: {str(e)}")
print()

# 5. City Analysis for Donors
print("5️⃣  DONOR DISTRIBUTION BY CITY")
print("-" * 80)
cities = DonorDetails.objects.filter(is_available=True, user__profile__phone_e164__isnull=False).exclude(user__profile__phone_e164='').values('city').annotate(count=Count('id')).order_by('-count')
if cities:
    for city in cities[:10]:
        blood_groups = DonorDetails.objects.filter(city=city['city'], is_available=True, user__profile__phone_e164__isnull=False).exclude(user__profile__phone_e164='').values('blood_group').annotate(count=Count('id')).order_by('-count')
        print(f"   📍 {city['city']}: {city['count']} available donors")
        for bg in blood_groups:
            print(f"      - {bg['blood_group']}: {bg['count']} donors")
else:
    print("   ❌ No available donors with phone in any city")
print()

print("="*80)
print("END OF DEBUG CHECK")
print("="*80 + "\n")

print("📋 RECOMMENDATIONS:")
print("-" * 80)
if not sms_api_key:
    print("   1. Set VEINLINE_SMS_API_KEY in environment or settings")
else:
    print("   1. ✅ VEINLINE_SMS_API_KEY is configured")

if donors_with_phone == 0:
    print("   2. Have donors add their phone number to their profile")
else:
    print(f"   2. ✅ {donors_with_phone} donors have phone numbers")

if total_donors == 0:
    print("   3. Create test donor accounts and mark them as available")
else:
    print(f"   3. ✅ {total_donors} donors exist")

print()
