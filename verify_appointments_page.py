import os
import django
from django.test import Client

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'veinline_backend.settings')
django.setup()

client = Client()

print("Testing appointments page...")
response = client.get('/appointments/')
print(f"Status: {response.status_code}")

if response.status_code == 200:
    content = response.content.decode()
    checks = [
        ('slotsContainer', 'Slots container'),
        ('myAppointments', 'My appointments container'),
        ('Book a Donation', 'Page title'),
        ('loadAllSlots', 'JavaScript function'),
    ]
    
    print("\n✅ Page checks:")
    for check, desc in checks:
        if check in content:
            print(f"   ✅ {desc}")
        else:
            print(f"   ❌ {desc}")
else:
    print(f"❌ Failed to load page: {response.status_code}")
